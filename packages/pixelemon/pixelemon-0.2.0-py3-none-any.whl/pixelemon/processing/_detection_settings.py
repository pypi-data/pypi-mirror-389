from math import ceil, pi, sqrt

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, Field

from pixelemon.constants import FWHM_TO_SIGMA
from pixelemon.logging import pixelemon_LOG

MIN_DEBLEND_MESH_COUNT = 1
MAX_DEBLEND_MESH_COUNT = 64

DEFAULT_DETECTION_THRESHOLD_SIGMA = 2.0
POINT_SOURCE_MIN_PIXEL_COUNT = 5
POINT_SOURCE_DEBLEND_MESH_COUNT = 32
POINT_SOURCE_DEBLEND_CONTRAST = 0.0005
POINT_SOURCE_FWHM = ceil(sqrt(POINT_SOURCE_MIN_PIXEL_COUNT / pi) * 2)
POINT_SOURCE_ARRAY_SIZE = int(6 * POINT_SOURCE_FWHM * FWHM_TO_SIGMA) | 1  # Ensure odd size
STREAK_SOURCE_MIN_PIXEL_COUNT = 5
STREAK_SOURCE_DEBLEND_MESH_COUNT = 1
STREAK_SOURCE_DEBLEND_CONTRAST = 1.0
STREAK_FWHM = 3
STREAK_SOURCE_ARRAY_SIZE = 31


class DetectionSettings(BaseModel):

    detection_threshold_sigma: float = Field(..., description="The sigma threshold for object detection")
    min_pixel_count: int = Field(
        ...,
        description="The minimum number of connected pixels to consider an object detected",
    )
    deblend_mesh_count: int = Field(
        ...,
        description="The number of meshes used for deblending overlapping objects",
        ge=MIN_DEBLEND_MESH_COUNT,
        le=MAX_DEBLEND_MESH_COUNT,
    )
    deblend_contrast: float = Field(
        ...,
        description="The contrast ratio used for deblending overlapping objects",
        ge=0.0,
        le=1.0,
    )
    merge_small_detections: bool = Field(
        ...,
        description="Whether to merge small detections with nearby larger ones",
    )

    kernel_array_size: int = Field(
        ...,
        description="The size of the Gaussian kernel array for detection",
    )

    full_width_half_maximum: int = Field(
        ...,
        description="The full width at half maximum (FWHM) for the Gaussian kernel",
    )

    @classmethod
    def point_source_defaults(cls) -> "DetectionSettings":
        pixelemon_LOG.info(f"Point source detection threshold set to {DEFAULT_DETECTION_THRESHOLD_SIGMA} sigma")
        pixelemon_LOG.info(f"Point source minimum pixel count set to {POINT_SOURCE_MIN_PIXEL_COUNT} pixels")
        pixelemon_LOG.info(f"Point source deblend mesh count set to {POINT_SOURCE_DEBLEND_MESH_COUNT} meshes")
        pixelemon_LOG.info(f"Point source deblend contrast set to {POINT_SOURCE_DEBLEND_CONTRAST}")
        pixelemon_LOG.info(f"Point source array size set to {POINT_SOURCE_ARRAY_SIZE} pixels")
        pixelemon_LOG.info(f"Point source FWHM set to {POINT_SOURCE_FWHM}")
        return cls(
            detection_threshold_sigma=DEFAULT_DETECTION_THRESHOLD_SIGMA,
            min_pixel_count=POINT_SOURCE_MIN_PIXEL_COUNT,
            deblend_mesh_count=POINT_SOURCE_DEBLEND_MESH_COUNT,
            deblend_contrast=POINT_SOURCE_DEBLEND_CONTRAST,
            merge_small_detections=False,
            kernel_array_size=POINT_SOURCE_ARRAY_SIZE,
            full_width_half_maximum=POINT_SOURCE_FWHM,
        )

    @classmethod
    def streak_source_defaults(cls) -> "DetectionSettings":
        pixelemon_LOG.info(f"Streak source detection threshold set to {DEFAULT_DETECTION_THRESHOLD_SIGMA} sigma")
        pixelemon_LOG.info(f"Streak source minimum pixel count set to {STREAK_SOURCE_MIN_PIXEL_COUNT} pixels")
        pixelemon_LOG.info(f"Streak source deblend mesh count set to {STREAK_SOURCE_DEBLEND_MESH_COUNT} meshes")
        pixelemon_LOG.info(f"Streak source deblend contrast set to {STREAK_SOURCE_DEBLEND_CONTRAST}")
        return cls(
            detection_threshold_sigma=DEFAULT_DETECTION_THRESHOLD_SIGMA,
            min_pixel_count=STREAK_SOURCE_MIN_PIXEL_COUNT,
            deblend_mesh_count=STREAK_SOURCE_DEBLEND_MESH_COUNT,
            deblend_contrast=STREAK_SOURCE_DEBLEND_CONTRAST,
            merge_small_detections=True,
            kernel_array_size=STREAK_SOURCE_ARRAY_SIZE,
            full_width_half_maximum=STREAK_FWHM,
        )

    @property
    def gaussian_kernel(self) -> npt.NDArray[np.float32]:
        ax = np.array(self.kernel_array_size) - self.kernel_array_size // 2
        xx, yy = np.meshgrid(ax, ax)
        sigma = self.full_width_half_maximum * FWHM_TO_SIGMA
        kernel = np.exp(-(xx**2 + yy**2) / (2.0 * sigma**2))
        return kernel / kernel.sum()
