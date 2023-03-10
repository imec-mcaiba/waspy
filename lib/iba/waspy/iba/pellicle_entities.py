from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional

from pydantic import BaseModel, Field, validator
from waspy.drivers.caen import DetectorMetadata


class Detector(DetectorMetadata):
    identifier: str = Field(
        description="This will be used in the filenames for storage and in the plots for titles")


class PellicleDriverUrls(BaseModel):
    aml_x_y: str
    aml_phi_zeta: str
    aml_det_theta: str
    caen: str
    motrona_charge: str


class Plot(BaseModel):
    title: str
    points: List[int]


class PellicleData(BaseModel):
    aml_x_y: Dict
    aml_phi_zeta: Dict
    aml_det_theta: Dict
    caen: Dict
    motrona: Dict
    histograms: Dict[str, List[int]] = Field(description="Maps detector name to resulting dataset")
    measuring_time_sec: float
    accumulated_charge: float


class PellicleJournal(BaseModel):
    start_time: datetime
    end_time: datetime
    x: float
    y: float
    det: float
    theta: float
    phi: float
    zeta: float
    histograms: Dict[str, List[int]] = Field(description="Maps detector name to resulting dataset")
    measuring_time_sec: float
    accumulated_charge: float


def get_pellicle_journal(rbs_data: PellicleData, start_time: datetime) -> PellicleJournal:
    return PellicleJournal(
        x=rbs_data.aml_x_y["motor_1_position"], y=rbs_data.aml_x_y["motor_2_position"],
        phi=rbs_data.aml_phi_zeta["motor_1_position"], zeta=rbs_data.aml_phi_zeta["motor_2_position"],
        det=rbs_data.aml_det_theta["motor_1_position"], theta=rbs_data.aml_det_theta["motor_2_position"],
        accumulated_charge=rbs_data.accumulated_charge, measuring_time_sec=rbs_data.measuring_time_sec,
        histograms=rbs_data.histograms, start_time=start_time, end_time=datetime.now()
    )


class PositionCoordinates(BaseModel):
    x: Optional[float]
    y: Optional[float]
    phi: Optional[float]
    zeta: Optional[float]
    detector: Optional[float]
    theta: Optional[float]

    def __str__(self):
        return "position_{x}_{y}_{phi}_{zeta}_{det}_{theta}".format(x=self.x, y=self.y, phi=self.phi, zeta=self.zeta,
                                                                    det=self.detector, theta=self.theta)


class Graph(BaseModel):
    title: str
    plots: List[Plot]
    x_label: Optional[str]
    y_label: Optional[str]


class GraphGroup(BaseModel):
    graphs: List[Graph]
    title: str


class PellicleHistogramGraphData(BaseModel):
    graph_title: str
    histogram_data: Dict[str, List[int]] = Field(
        description="For each item in this list, a new graph is created.  There is 1 plot per graph")
    x_label: str = "energy level"
    y_label: str = "yield"


class PellicleHistogramGraphDataSet(BaseModel):
    """
        The amount of items in the super-list of histograms determines how many graphs will be created. The data in the"
        sub-list of histograms will be plotted on the same graph. There can be more than 1 plot per graph")
        Example:
            histograms = [ [[0,1,2], [1,2,3]], [[2,3,4], [3,4,5]], [[4,5,6], [5,6,7]] ]
                           ---- graph 1 ----   ---- graph 2 -----  ---- graph 3 -----
                           -plot 1-  -plot 2-  -plot 1-  -plot 2-  - plot 1-  -plot 2-
    """

    graph_title: str
    histograms: List[Dict[str, List[int]]]
    x_label: str = "energy level"
    y_label: str = "yield"


class CoordinateEnum(str, Enum):
    zeta = "zeta"
    theta = "theta"
    phi = "phi"
    none = "none"


class Window(BaseModel):
    start: int
    end: int

    @validator('start', allow_reuse=True)
    def start_larger_than_zero(cls, start):
        if not start >= 0:
            raise ValueError('start must be positive')
        return start

    @validator('end', allow_reuse=True)
    def end_larger_than_zero(cls, end):
        if not end >= 0:
            raise ValueError('end must be positive')
        return end

    @validator('end', allow_reuse=True)
    def start_must_be_smaller_than_end(cls, end, values):
        if 'start' not in values:
            return
        if not values['start'] < end:
            raise ValueError("end must be larger then start")
        return end

