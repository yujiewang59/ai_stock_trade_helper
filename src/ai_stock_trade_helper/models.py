"""数据模型定义"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class StockAnalysisMetrics(BaseModel):
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market_cap: Optional[float] = Field(None, description="市值（亿元）")
    roe: Optional[float] = Field(None, description="净资产收益率 (%)")
    net_margin: Optional[float] = Field(None, description="销售净利率 (%)")
    debt_ratio: Optional[float] = Field(None, description="资产负债率 (%)")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    industry: Optional[str] = Field(None, description="所属行业")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="分析时间戳")

class UserStockHold(BaseModel):
    symbol: str = Field(..., description="股票代码")
    shares: float = Field(..., description="持股数量")
    current_price: Optional[float] = Field(None, description="当前价格")

class StockInfo(BaseModel):
    """股票基本信息"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")

class AnalysisResult(BaseModel):
    """单个分析结果"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    recommendation: str = Field(..., description="操作建议：buy/sell/hold")
    position_size: Optional[float] = Field(None, description="建议仓位大小（0-1）")
    confidence: float = Field(..., description="操作置信度（0-1）")
    reason: Optional[str] = Field(None, description="原因分析报告")


class MultiStockDecision(BaseModel):
    """多股综合决策"""
    decisions: List[AnalysisResult] = Field(..., description="所有股票的投资决策")
    summary: str = Field(..., description="综合分析总结")
    overall_recommendation: str = Field(..., description="整体投资建议")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="分析时间")


class StockAnalysisState(BaseModel):
    """股票分析状态"""
    user_assets: Optional[float] = Field(None, description="用户总资产")
    user_stock_holds: Optional[List[UserStockHold]] = Field(None, description="用户持仓信息")
    industry: Optional[str] = Field(None, description="待分析的行业名称")
    industry_label: Optional[str] = Field(None, description="行业标签，用于索引行业数据")
    risk_level: Optional[str] = Field(None, description="投资者风险承受能力：low/medium/high")
    stock_codes: Optional[List[StockInfo]] = Field(None, description="待分析的股票代码列表")
    base_analysis_results: Optional[List[AnalysisResult]] = Field(None, description="基本面分析结果")
    technical_analysis_results: Optional[List[AnalysisResult]] = Field(None, description="技术面分析结果")
    sentiment_analysis_results: Optional[List[AnalysisResult]] = Field(None, description="市场情绪分析结果")
    investment_decisions: Optional[List[AnalysisResult]] = Field(None, description="综合投资决策")
    multi_stock_decision: Optional[MultiStockDecision] = Field(None, description="多股分析最终决策")


class TaskRequest(BaseModel):
    """任务请求参数"""
    industry: str
    industry_label: str
    user_assets: float
    user_stock_holds: list[UserStockHold]
    risk_level: str