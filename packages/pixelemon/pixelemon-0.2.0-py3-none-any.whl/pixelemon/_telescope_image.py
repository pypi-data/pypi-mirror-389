from datetime import datetime
from pathlib import Path

import numpy as np
import numpy.typing as npt
import sep  # type: ignore
from astropy.coordinates import SkyCoord  # type: ignore
from astropy.io import fits  # type: ignore
from astropy.wcs import WCS  # type: ignore
from astropy.wcs.utils import fit_wcs_from_points  # type: ignore
from pydantic import BaseModel, Field

from pixelemon._plate_solve import PlateSolve, TetraSolver
from pixelemon._telescope import Telescope
from pixelemon.constants import PERCENT_TO_DECIMAL
from pixelemon.logging import pixelemon_LOG
from pixelemon.processing import MIN_BACKGROUND_MESH_COUNT, BackgroundSettings, Detections, DetectionSettings


class TelescopeImage(BaseModel):
    _original_array: npt.NDArray[np.float32] | None = None
    _processed_array: npt.NDArray[np.float32] | None = None
    _plate_solve: PlateSolve | None = None
    _detections: Detections | None = None
    _background: sep.Background | None = None
    _background_removed: bool = False
    epoch: datetime | None = None
    telescope: Telescope | None = None
    _wcs: WCS | None = None
    image_scale: float = Field(default=1.0, description="The image scale due to cropping")
    background_settings: BackgroundSettings = Field(default=BackgroundSettings())
    detection_settings: DetectionSettings = Field(default=DetectionSettings.streak_source_defaults())

    @classmethod
    def from_fits_file(cls, file_path: Path, telescope: Telescope) -> "TelescopeImage":
        with fits.open(file_path) as hdul:
            img = cls()
            assert hasattr(hdul[0], "header")
            header = getattr(hdul[0], "header")
            img._wcs = WCS(header)
            img.epoch = datetime.fromisoformat(header["DATE-OBS"])
            img.telescope = telescope
            img._original_array = getattr(hdul[0], "data").astype(np.float32)
            assert img._original_array is not None
            actual_ratio = img._original_array.shape[1] / img._original_array.shape[0]
            if not np.isclose(img.telescope.aspect_ratio, actual_ratio, rtol=1e-2):
                pixelemon_LOG.warning("Trimming image to match expected aspect")
                new_width = int(img._original_array.shape[0] * img.telescope.aspect_ratio)
                img._original_array = img._original_array[:, 0:new_width]
                img._original_array = np.ascontiguousarray(img._original_array)
            assert img._original_array is not None
            img._processed_array = img._original_array.copy()
        pixelemon_LOG.info(f"Loaded {img._original_array.shape} image from {file_path} with epoch {img.epoch}")
        return img

    def write_to_fits_file(self, file_path: Path):
        if self._processed_array is None:
            raise ValueError("Image array is not loaded.")
        fits.writeto(file_path, self._processed_array.astype("uint8"), overwrite=True)
        pixelemon_LOG.info(f"Saved processed image to {file_path}")

    def crop(self, crop_percent: float):
        if self._original_array is None:
            raise ValueError("Image array is not loaded.")

        crop_fraction = crop_percent * PERCENT_TO_DECIMAL
        height, width = self._original_array.shape
        crop_height = int(height * crop_fraction / 2)
        crop_width = int(width * crop_fraction / 2)
        self._processed_array = np.ascontiguousarray(
            self._original_array[crop_height : height - crop_height, crop_width : width - crop_width]
        )
        pixelemon_LOG.info(f"Image cropped to {self._processed_array.shape}")
        self.image_scale = self.image_scale * (1.0 - crop_fraction)
        new_fov = f"{self.horizontal_field_of_view:.2f} x {self.vertical_field_of_view:.2f} degrees"  # noqa: E231
        pixelemon_LOG.info(f"New field of view is {new_fov}")
        self._plate_solve = None
        self._detections = None
        self._background = None
        self._background_removed = False

    def get_brightest_stars(self, count: int) -> Detections:
        detections = self.detections.stars
        sorted_detections = sorted(detections, key=lambda det: det.total_flux, reverse=True)
        return_count = min(count, len(sorted_detections))
        return Detections(sorted_detections[:return_count])

    @property
    def background(self) -> sep.Background:
        if self._processed_array is None:
            raise ValueError("Image array is not loaded.")

        if self._background is None:

            bw = max(
                MIN_BACKGROUND_MESH_COUNT, int(self._processed_array.shape[1] / self.background_settings.mesh_count)
            )
            bh = max(
                MIN_BACKGROUND_MESH_COUNT, int(self._processed_array.shape[0] / self.background_settings.mesh_count)
            )
            pixelemon_LOG.info(f"Background mesh size: {bw}x{bh}")

            self._background = sep.Background(
                self._processed_array,
                bw=bw,
                bh=bh,
                fw=self.background_settings.filter_size,
                fh=self.background_settings.filter_size,
                fthresh=self.background_settings.detection_threshold,
            )

        return self._background

    def remove_background(self):
        if self._processed_array is None:
            raise ValueError("Image array is not loaded.")
        self._processed_array = self._processed_array - self.background
        self._background_removed = True

    def reset(self):
        if self._original_array is None:
            raise ValueError("Image array is not loaded.")
        self._processed_array = self._original_array.copy()
        self.image_scale = 1.0
        self._background = None
        self._detections = None
        self._plate_solve = None
        self._background_removed = False
        pixelemon_LOG.info("Image reset to original")

    @property
    def horizontal_field_of_view(self) -> float:
        if self.telescope is None:
            raise ValueError("Telescope is not set.")
        return self.telescope.horizontal_field_of_view * self.image_scale

    @property
    def vertical_field_of_view(self) -> float:
        if self.telescope is None:
            raise ValueError("Telescope is not set.")
        return self.telescope.vertical_field_of_view * self.image_scale

    @property
    def diagonal_field_of_view(self) -> float:
        if self.telescope is None:
            raise ValueError("Telescope is not set.")
        return self.telescope.diagonal_field_of_view * self.image_scale

    @property
    def detections(self):
        if self._processed_array is None:
            raise ValueError("Image array is not loaded.")

        if self._detections is None:
            objects = sep.extract(
                self._processed_array,
                thresh=self.detection_settings.detection_threshold_sigma * self.background.globalrms,
                minarea=self.detection_settings.min_pixel_count,
                filter_kernel=self.detection_settings.gaussian_kernel,
                deblend_nthresh=self.detection_settings.deblend_mesh_count,
                deblend_cont=self.detection_settings.deblend_contrast,
                clean=self.detection_settings.merge_small_detections,
                segmentation_map=False,
            )

            self._detections = Detections.from_sep_extract(objects)

        return self._detections

    @property
    def plate_solve(self) -> PlateSolve | None:
        if self._processed_array is None:
            raise ValueError("Image array is not loaded.")
        if self.telescope is None:
            raise ValueError("Telescope is not set.")

        if not self._background_removed:
            self.remove_background()

        if self._plate_solve is None:

            fov = f"{self.horizontal_field_of_view:.2f} x {self.vertical_field_of_view:.2f} degrees"  # noqa: E231
            pixelemon_LOG.info(f"Solving {len(self.detections.stars)} detected stars and FOV of {fov}")

            tetra_solve = TetraSolver().solve_from_centroids(
                self.get_brightest_stars(TetraSolver().settings.verification_star_count).y_x_array,
                size=self._processed_array.shape,
                fov_estimate=self.diagonal_field_of_view,
                return_matches=True,
            )

            if tetra_solve["RA"] is None:
                pixelemon_LOG.warning("Plate solve failed.")
                return None
            else:
                plate_solve = PlateSolve.model_validate(tetra_solve)
                pixel_scale = self.telescope.horizontal_pixel_scale
                assert self._wcs is not None

                # seed the WCS to improve chances of solution with fit_wcs_from_points
                self._wcs.wcs.crpix = [self._processed_array.shape[1] / 2, self._processed_array.shape[0] / 2]
                self._wcs.wcs.crval = [plate_solve.right_ascension, plate_solve.declination]
                self._wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
                self._wcs.wcs.cunit = ["deg", "deg"]
                theta = np.deg2rad(-plate_solve.roll)
                cd11 = -pixel_scale * np.cos(theta)
                cd12 = pixel_scale * np.sin(theta)
                cd21 = pixel_scale * np.sin(theta)
                cd22 = pixel_scale * np.cos(theta)
                self._wcs.wcs.cd = np.array([[cd11, cd12], [cd21, cd22]], dtype=float)

                # invert matched centroids for WCS fitting
                yx = np.array(tetra_solve["matched_centroids"])
                x, y = yx[:, 1], self._processed_array.shape[0] - 1 - yx[:, 0]
                ra_dec = np.array(tetra_solve["matched_stars"])

                # fit WCS from matched stars
                sky = SkyCoord(ra=ra_dec[:, 0], dec=ra_dec[:, 1], unit="deg")
                self._wcs = fit_wcs_from_points((x, y), sky, sip_degree=5)
                self._plate_solve = plate_solve

        return self._plate_solve
