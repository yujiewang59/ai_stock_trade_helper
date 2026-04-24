"""股票分析工作流"""
from crewai.flow.flow import Flow, listen, start, and_
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import logging

from ai_stock_trade_helper.models import MultiStockDecision, StockAnalysisState, AnalysisResult, StockInfo
from ai_stock_trade_helper.multi_dimension_crew import BaseAnalysisCrew, SentimentAnalysisCrew, TechnicalAnalysisCrew
from ai_stock_trade_helper.synthesis_crew import SynthesisCrew
from ai_stock_trade_helper.multi_stock_crew import MultiStockCrew
from ai_stock_trade_helper.tools.screen_stocks import screen_top_stocks_by_industry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class StockAnalysisFlow(Flow[StockAnalysisState]):
    """股票分析工作流 - 编排并行执行基本面、技术面、市场情绪分析阶段"""

    @start()
    def setup_analysis(self):
        """设置分析初始状态，根据行业信息筛选符合条件的股票"""
        logger.info(f"开始股票分析流程设置")
        
        # 检查是否提供了行业信息
        if not self.state.industry:
            logger.warning("未提供行业信息，检查是否有预设股票代码")
            if self.state.stock_codes:
                logger.info(f"使用预设的股票代码进行分析: {self.state.stock_codes}")
                return f"准备分析以下股票: {', '.join(self.state.stock_codes)}"
            else:
                logger.error("既未提供行业信息，也未提供股票代码")
                raise ValueError("必须提供行业名称或股票代码")
        
        # 根据行业信息进行股票筛选
        logger.info(f"根据行业'{self.state.industry}'进行股票筛选")

        user_stocks = [stock.symbol for stock in self.state.user_stock_holds] if len(self.state.user_stock_holds)>0 else []
        
        try:
            # 进行股票筛选，合并用户持仓的股票代码
            stock_codes = screen_top_stocks_by_industry(
                industry_label=self.state.industry_label,
                user_stock_codes=user_stocks,
                top_n=20,
                min_market_cap=30,      # 流通市值 >= 30亿
                min_roe=8,              # ROE >= 8%
                min_net_margin=3,       # 销售净利率 >= 3%
                max_debt_ratio=70       # 资产负债率 <= 70%
            )
            
            if not stock_codes:
                logger.error(f"从行业'{self.state.industry}'未能筛选出符合条件的股票")
                raise ValueError(f"无法为行业'{self.state.industry}'筛选出符合条件的股票")
            
            # 更新state中的股票代码
            self.state.stock_codes = stock_codes
            
            logger.info(f"行业筛选完成：从'{self.state.industry}'行业筛选出 {len(stock_codes)} 只符合条件的股票，准备进入多维度分析阶段")
            return stock_codes
        
        except Exception as e:
            logger.error(f"股票筛选过程中出现错误: {e}", exc_info=True)
            raise ValueError(f"股票筛选失败: {e}")

    @listen(setup_analysis)
    async def base_analysis_stage(self, stock_codes: List[StockInfo]):
        """第一支：基本面分析 - 并行分析所有股票的基本面"""
        logger.info("进入基本面分析阶段（并行执行）")
        logger.info(f"使用 kickoff_for_each 并行处理 {len(stock_codes)} 只股票的基本面分析")
        
        try:
            # 构建输入数组
            inputs = [{"stock_code": stock.stock_code, "stock_name": stock.stock_name, "industry": self.state.industry} for stock in stock_codes]

            self.state.base_analysis_results = []
            
            # 使用 kickoff_for_each 并行执行基本面分析
            base_results = await BaseAnalysisCrew().crew().akickoff_for_each(inputs=inputs)

            # 处理返回结果并保存到状态
            for raw_result in base_results:
                # 从 crewai 返回的结果中提取数据
                result_data = AnalysisResult(**json.loads(raw_result.raw))
                self.state.base_analysis_results.append(result_data)
            
            logger.info(f"基本面分析完成，共 {len(self.state.base_analysis_results)} 个结果已保存")
            return f"基本面分析完成，处理 {len(self.state.base_analysis_results)} 只股票"
        except Exception as e:
            logger.error(f"基本面分析失败: {e}", exc_info=True)
            return f"基本面分析失败: {e}"

    @listen(setup_analysis)
    async def technical_analysis_stage(self, stock_codes: List[StockInfo]):
        """第二支：技术面分析 - 并行分析所有股票的技术面"""
        logger.info("进入技术面分析阶段（并行执行）")
        logger.info(f"使用 kickoff_for_each 并行处理 {len(stock_codes)} 只股票的技术面分析")
        
        try:
            # 构建输入数组
            inputs = [{"stock_code": stock.stock_code, "stock_name": stock.stock_name, "industry": self.state.industry} for stock in stock_codes]
            
            self.state.technical_analysis_results = []
            # 使用 kickoff_for_each 并行执行技术面分析
            technical_results = await TechnicalAnalysisCrew().crew().akickoff_for_each(inputs=inputs)
            
            # 处理返回结果并保存到状态
            for raw_result in technical_results:
                result_data = AnalysisResult(**json.loads(raw_result.raw))
                self.state.technical_analysis_results.append(result_data)
            
            logger.info(f"技术面分析完成，共 {len(self.state.technical_analysis_results)} 个结果已保存")
            return f"技术面分析完成，处理 {len(self.state.technical_analysis_results)} 只股票"
        except Exception as e:
            logger.error(f"技术面分析失败: {e}", exc_info=True)
            return f"技术面分析失败: {e}"

    @listen(setup_analysis)
    async def sentiment_analysis_stage(self, stock_codes: List[StockInfo]):
        """第三支：市场情绪分析 - 并行分析所有股票的市场情绪"""
        logger.info("进入市场情绪分析阶段（并行执行）")
        logger.info(f"使用 kickoff_for_each 并行处理 {len(stock_codes)} 只股票的市场情绪分析")
        
        try:
            # 构建输入数组
            inputs = [{"stock_code": stock.stock_code, "stock_name": stock.stock_name, "industry": self.state.industry} for stock in stock_codes]
            
            self.state.sentiment_analysis_results = []
            # 使用 kickoff_for_each 并行执行市场情绪分析
            sentiment_results = await SentimentAnalysisCrew().crew().akickoff_for_each(inputs=inputs)

            # 处理返回结果并保存到状态
            for raw_result in sentiment_results:
                result_data = AnalysisResult(**json.loads(raw_result.raw))
                self.state.sentiment_analysis_results.append(result_data)
            
            logger.info(f"市场情绪分析完成，共 {len(self.state.sentiment_analysis_results)} 个结果已保存")
            return f"市场情绪分析完成，处理 {len(self.state.sentiment_analysis_results)} 只股票"
        except Exception as e:
            logger.error(f"市场情绪分析失败: {e}", exc_info=True)
            return f"市场情绪分析失败: {e}"

    @listen(and_(base_analysis_stage, technical_analysis_stage, sentiment_analysis_stage))
    async def synthesis_analysis(self):
        """第二段：综合分析 - 等待三个并行分析都完成后进行综合决策"""
        logger.info("三个分析阶段已全部完成，进入综合分析阶段")
        
        try:
            # 为每只股票构建包含三维分析结果的综合分析输入
            inputs = []
            for stock in self.state.stock_codes:
                code = stock.stock_code
                stock_name = stock.stock_name
                # 查找该股票的三维分析结果
                base_result = next((r for r in self.state.base_analysis_results if r.stock_code == code), None)
                technical_result = next((r for r in self.state.technical_analysis_results if r.stock_code == code), None)
                sentiment_result = next((r for r in self.state.sentiment_analysis_results if r.stock_code == code), None)
                
                # 构建分析结果摘要
                analysis_results = f"""
                基本面分析结果：
                - decision: {base_result.recommendation if base_result else '无'}
                - confidence: {base_result.confidence if base_result else 0}
                - reason: {base_result.reason if base_result else '无'}

                技术面分析结果：
                - decision: {technical_result.recommendation if technical_result else '无'}
                - confidence: {technical_result.confidence if technical_result else 0}
                - reason: {technical_result.reason if technical_result else '无'}

                市场情绪分析结果：
                - decision: {sentiment_result.recommendation if sentiment_result else '无'}
                - confidence: {sentiment_result.confidence if sentiment_result else 0}
                - reason: {sentiment_result.reason if sentiment_result else '无'}
                """
                
                inputs.append({
                    "stock_code": code,
                    "stock_name": stock_name,
                    "industry": self.state.industry,
                    "risk_level": self.state.risk_level,
                    "analysis_results": analysis_results
                })
            
            self.state.investment_decisions = []
            
            # 使用 kickoff_for_each 并行执行综合分析
            synthesis_results = await SynthesisCrew().crew().akickoff_for_each(inputs=inputs)
            
            # 处理返回结果并保存到状态
            for raw_result in synthesis_results:
                # 从 crewai 返回的结果中提取数据
                result_data = AnalysisResult(**json.loads(raw_result.raw))
                self.state.investment_decisions.append(result_data)
            
            logger.info(f"综合分析完成，共生成 {len(self.state.investment_decisions)} 个投资决策")
            return f"综合分析完成，生成 {len(self.state.investment_decisions)} 个投资决策"
        except Exception as e:
            logger.error(f"综合分析阶段失败: {e}", exc_info=True)
            return f"综合分析失败: {e}"

    @listen(synthesis_analysis)
    async def multi_stock_analysis(self):
        """第三段：多股分析 - 综合所有股票的决策生成行业级投资策略"""
        logger.info("进入多股分析阶段")
        
        # 使用综合分析的结果生成多股决策输入
        decisions_summary = []
        for decision in self.state.investment_decisions:
            summary = f"""
            stock_code: {decision.stock_code}
            stock_name: {decision.stock_name}
            recommendation: {decision.recommendation}
            confidence: {decision.confidence}
            reason: {decision.reason}
            """
            decisions_summary.append(summary)

        data = {
            "multi_stock_decisions": decisions_summary,
            "risk_level": self.state.risk_level,
            "industry": self.state.industry,
            "user_assets": self.state.user_assets,
            "user_stock_holds": [hold.model_dump() for hold in self.state.user_stock_holds]
        }

        inputs = data
        
        # 执行多股分析crew
        try:
            result = await MultiStockCrew().crew().akickoff(inputs=inputs)
            logger.info("多股综合分析完成")
            result = MultiStockDecision(**json.loads(result.raw))
            return result.model_dump() if result else "多股分析完成，但未能正确解析结果"
        
        except Exception as e:
            logger.error(f"多股分析失败: {e}", exc_info=True)
            return f"多股分析失败: {e}"

