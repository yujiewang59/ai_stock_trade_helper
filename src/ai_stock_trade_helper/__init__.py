"""AI股票分析助手 - 基于CrewAI的多智能体股票分析系统"""

__version__ = "0.1.0"

from .main import run
from .flow import StockAnalysisFlow, StockAnalysisState
from .models import (
    AnalysisResult,
    MultiStockDecision,
)

__all__ = [
    "run",
    "StockAnalysisFlow",
    "StockAnalysisState",
    "AnalysisResult",
    "MultiStockDecision",
]
