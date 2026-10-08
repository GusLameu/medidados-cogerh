"""
Tipos compartilhados entre os componentes do dashboard.
"""
from dataclasses import dataclass
from typing import Any, Optional, TypeAlias

from matplotlib.axes import Axes
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Wedge


MetricCounts: TypeAlias = dict[str, int]
GeneralIndicators: TypeAlias = dict[str, Any]
WedgeInfo: TypeAlias = dict[str, Any]
WedgeInfoMap: TypeAlias = dict[Wedge, WedgeInfo]
PieChartPosition: TypeAlias = tuple[int, int]
PieChartLegendList: TypeAlias = list[Legend]


@dataclass
class MainChartResult:
    """
    Referências aos elementos criados no gráfico temporal principal.
    """

    flow_axis: Axes
    secondary_axis: Optional[Axes]
    flow_line: Line2D
    secondary_line: Optional[Line2D]
    legend: Legend
    mean_flow: float