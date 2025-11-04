import numpy as np
from numpy import typing as npt
from pydantic import BaseModel, Field, RootModel


class Detection(BaseModel):
    x_centroid: float = Field(..., description="X coordinate of the detection centroid in pixels")
    y_centroid: float = Field(..., description="Y coordinate of the detection centroid in pixels")
    semi_major_axis: float = Field(..., description="Semi-major axis of the detection in pixels")
    semi_minor_axis: float = Field(..., description="Semi-minor axis of the detection in pixels")
    angle_to_horizon: float = Field(..., description="Orientation angle of the detection in degrees")
    total_flux: float = Field(..., description="Total flux of the detection in arbitrary units")

    @classmethod
    def from_sep_object(cls, obj: dict) -> "Detection":
        return cls(
            x_centroid=obj["x"],
            y_centroid=obj["y"],
            semi_major_axis=obj["a"],
            semi_minor_axis=obj["b"],
            angle_to_horizon=obj["theta"],
            total_flux=obj["flux"],
        )

    @property
    def elongation(self) -> float:
        return self.semi_major_axis / self.semi_minor_axis


class Detections(RootModel[list[Detection]]):

    @classmethod
    def from_sep_extract(cls, objects: list[dict]) -> "Detections":
        detections = [Detection.from_sep_object(obj) for obj in objects]
        return cls(detections)

    def __len__(self) -> int:
        return len(self.root)

    def __getitem__(self, index: int) -> Detection:
        return self.root[index]

    def __iter__(self):
        return iter(self.root)

    def append(self, detection: Detection) -> None:
        self.root.append(detection)

    @property
    def y_x_array(self) -> npt.NDArray[np.float32]:
        return np.array([[det.y_centroid, det.x_centroid] for det in self.root], dtype=np.float32)

    @property
    def x_y_array(self) -> npt.NDArray[np.float32]:
        return np.array([[det.x_centroid, det.y_centroid] for det in self.root], dtype=np.float32)

    @property
    def elongation_array(self) -> npt.NDArray[np.float32]:
        return np.array(
            [det.semi_major_axis / det.semi_minor_axis for det in self.root],
            dtype=np.float32,
        )

    @property
    def elongation_sigma(self) -> float:
        elongations = self.elongation_array
        return float(np.std(elongations))

    @property
    def average_elongation(self) -> float:
        elongations = self.elongation_array
        return float(np.mean(elongations))

    @property
    def stars(self) -> "Detections":
        mean_elongation = self.average_elongation
        sigma_elongation = self.elongation_sigma
        star_detections = [det for det in self if det.elongation <= (mean_elongation + sigma_elongation)]
        return Detections(star_detections)

    @property
    def satellites(self) -> "Detections":
        mean_elongation = self.average_elongation
        sigma_elongation = self.elongation_sigma
        satellite_detections = [det for det in self if det.elongation > (mean_elongation + sigma_elongation * 3)]
        return Detections(satellite_detections)
