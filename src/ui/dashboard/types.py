"""
Tipos compartilhados entre os componentes do dashboard.
"""
from typing import Any, TypeAlias

from matplotlib.legend import Legend
from matplotlib.patches import Wedge


MetricCounts: TypeAlias = dict[str, int]
GeneralIndicators: TypeAlias = dict[str, Any]
WedgeInfo: TypeAlias = dict[str, Any]
WedgeInfoMap: TypeAlias = dict[Wedge, WedgeInfo]
PieChartPosition: TypeAlias = tuple[int, int]
PieChartLegendList: TypeAlias = list[Legend]