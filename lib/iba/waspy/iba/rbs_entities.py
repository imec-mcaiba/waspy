from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Literal, Callable

import numpy as np
from pydantic import BaseModel, Field, validator
from waspy.drivers.caen import DetectorMetadata


class Detector(DetectorMetadata):
    identifier: str = Field(
        description="This will be used in the filenames for storage and in the plots for titles")


class RbsDriverUrls(BaseModel):
    aml_x_y: str
    aml_phi_zeta: str
    aml_det_theta: str
    caen: str
    motrona_charge: str


class Plot(BaseModel):
    title: str
    points: List[int]


class RbsData(BaseModel):
    aml_x_y: Dict
    aml_phi_zeta: Dict
    aml_det_theta: Dict
    caen: Dict
    motrona: Dict
    histograms: Dict[str, List[int]] = Field(description="Maps detector name to resulting dataset")
    measuring_time_sec: float
    accumulated_charge: float


class RbsJournal(BaseModel):
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


def get_rbs_journal(rbs_data: RbsData, start_time: datetime) -> RbsJournal:
    return RbsJournal(
        x=rbs_data.aml_x_y["motor_1_position"], y=rbs_data.aml_x_y["motor_2_position"],
        phi=rbs_data.aml_phi_zeta["motor_1_position"], zeta=rbs_data.aml_phi_zeta["motor_2_position"],
        det=rbs_data.aml_det_theta["motor_1_position"], theta=rbs_data.aml_det_theta["motor_2_position"],
        accumulated_charge=rbs_data.accumulated_charge, measuring_time_sec=rbs_data.measuring_time_sec,
        histograms=rbs_data.histograms, start_time=start_time, end_time=datetime.now()
    )


class AysFitResult(BaseModel):
    success: bool
    minimum: Optional[float]
    discrete_angles: List[float]
    discrete_yields: List[int]
    fit_func: Optional[Callable[[float], float]]


class AysJournal(BaseModel):
    start_time: datetime
    end_time: datetime
    rbs_journals: List[RbsJournal]
    fit: AysFitResult


class CmsYield(BaseModel):
    zeta: float
    theta: float
    energy_yield: int


class CmsJournal(BaseModel):
    start_time: datetime
    end_time: datetime
    cms_yields: List[CmsYield]


class ChannelingJournal(BaseModel):
    random: RbsJournal
    fixed: RbsJournal
    ays: List[AysJournal]


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


class HeatMap(BaseModel):
    title: str
    yields: List[CmsYield]


class Graph(BaseModel):
    title: str
    plots: List[Plot]
    x_label: Optional[str]
    y_label: Optional[str]


class GraphGroup(BaseModel):
    graphs: List[Graph]
    title: str


class RbsHistogramGraphData(BaseModel):
    graph_title: str
    histogram_data: Dict[str, List[int]] = Field(
        description="For each item in this list, a new graph is created.  There is 1 plot per graph")
    x_label: str = "energy level"
    y_label: str = "yield"


class RbsHistogramGraphDataSet(BaseModel):
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


class RecipeType(str, Enum):
    CHANNELING_MAP = "rbs_channeling_map"
    CHANNELING = "rbs_channeling"
    RANDOM = "rbs_random"
    ANGULAR_YIELD = "rbs_angular_yield"
    FIXED = "rbs_fixed"


class CoordinateEnum(str, Enum):
    zeta = "zeta"
    theta = "theta"
    phi = "phi"
    none = "none"


class CoordinateRange(BaseModel):
    name: CoordinateEnum
    start: float
    end: float
    increment: float

    class Config:
        use_enum_values = True

    @validator('increment')
    def increment_must_be_positive_and_non_zero(cls, increment):
        if not increment >= 0:
            raise ValueError('increment must be positive')
        return increment

    @validator('end')
    def start_must_be_smaller_than_end(cls, end, values):
        if 'start' not in values:
            return
        if not values['start'] <= end:
            raise ValueError('end must be larger than or equal to start')
        return end

    @classmethod
    def init_single(cls, name, start):
        return cls(name=name, start=start, end=start, increment=0.0)


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


class RbsChanneling(BaseModel):
    """
    The model for a channeling measurement. This is a combination of recipes. A number of yield optimizations will
    happen (ays - angular yield scan). Next, a fixed measurement and a random measurement are performed.
    The outputs of the configured detectors are then compared in a plot.
    """
    type: Literal[RecipeType.CHANNELING]
    sample: str
    name: str
    start_position: Optional[PositionCoordinates]
    yield_charge_total: int = Field(description="How much charge to accumulate per each step of ays")
    yield_coordinate_ranges: List[CoordinateRange]
    yield_integration_window: Window
    yield_optimize_detector_identifier: str
    compare_charge_total: int
    random_coordinate_range: CoordinateRange

    class Config:
        extra = 'forbid'


class RbsStepwiseLeast(BaseModel):
    """ The model for a yield minimization run. The sample will be moved along the vary_coordinate axis. For each step,
    the energy yield is calculated by integrating the histogram. Then the yields are fitted and the sample will be moved
    to the position with minimum yield """
    type: Literal[RecipeType.ANGULAR_YIELD]
    sample: str
    name: str
    start_position: Optional[PositionCoordinates]
    total_charge: int
    coordinate_range: CoordinateRange
    integration_window: Window
    optimize_detector_identifier: str


class RbsRandom(BaseModel):
    """ The model for a random measurement - the vary_coordinate will be changed"""
    type: Literal[RecipeType.RANDOM]
    sample: str
    name: str
    start_position: Optional[PositionCoordinates]
    charge_total: int
    coordinate_range: CoordinateRange


class RbsChannelingMap(BaseModel):
    """ The model for a channeling map measurement - the 2 vary_coordinates are changed depending on each other """
    type: Literal[RecipeType.CHANNELING_MAP]
    sample: str
    name: str
    start_position: Optional[PositionCoordinates]
    charge_total: int
    zeta_coordinate_range: CoordinateRange
    theta_coordinate_range: CoordinateRange
    yield_integration_window: Window
    optimize_detector_identifier: str


class RbsSingleStep(BaseModel):
    """ The model for a fixed measurement - all coordinates are kept the same"""
    type: Literal[RecipeType.FIXED]
    sample: str
    name: str
    charge_total: int


def get_positions_as_float(coordinate_range: CoordinateRange) -> List[float]:
    if coordinate_range.increment == 0:
        return [coordinate_range.start]
    coordinate_range = np.arange(coordinate_range.start, coordinate_range.end + coordinate_range.increment,
                                 coordinate_range.increment)
    numpy_array = np.around(coordinate_range, decimals=2)
    return [float(x) for x in numpy_array]


def get_positions_as_coordinate(coordinate_range: CoordinateRange) -> List[PositionCoordinates]:
    angles = get_positions_as_float(coordinate_range)
    positions = [PositionCoordinates.parse_obj({coordinate_range.name: angle}) for angle in angles]
    return positions
