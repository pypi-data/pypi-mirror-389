# thermohi/__init__.py
from .datalistio import DataList
from .thermoanalysis import KineticAnalysis, r_square_xy
from .plotting import FittingPlot
__version__ = '0.1.2'
__author__ = "Hikari Quicklime"
__email__ = "897237104@qq.com"
__all__ = ["DataList", "KineticAnalysis", "r_square_xy","FittingPlot"]