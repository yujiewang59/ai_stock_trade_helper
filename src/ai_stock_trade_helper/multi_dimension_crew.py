"""多维分析Crew"""
from pathlib import Path

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import yaml
from dotenv import load_dotenv
import os

from ai_stock_trade_helper.models import AnalysisResult
from ai_stock_trade_helper.tools.stock_tools import GetMarketSentimentTool, GetStockBasicInfoTool, GetStockTechnicalIndicatorsTool

from crewai.skills import discover_skills, activate_skill

load_dotenv()


llm = LLM(
    model="deepseek/deepseek-reasoner", 
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_BASE"),
    temperature=0.1,
    response_format={
        'type': 'json_object'
    },
    max_tokens=4096
)

skills = discover_skills(Path("skills"))

base_skill = [activate_skill(s) for s in skills if s.name == "base-analysis"]
senti_skill = [activate_skill(s) for s in skills if s.name == "sentiment-analysis"]
tech_skill = [activate_skill(s) for s in skills if s.name == "technical-analysis"]

@CrewBase
class BaseAnalysisCrew:
    """基本面分析Crew"""
    # agents_config = "config/agents.yaml"
    # tasks_config = "config/tasks.yaml"

    @agent
    def base_analyzer(self) -> Agent:
        return Agent(
            # config=self.agents_config["base_analyzer"],
            role="股票基本面分析专家",
            goal="深入分析公司的财务数据、盈利能力、成长性等基本面指标，为股票投资提供基于基本面的专业决策",
            backstory="""
                你是一位资深的财务分析师，拥有15年以上的股票基本面分析经验。
                你精于解读财务报表、分析盈利能力和成长潜力，能够通过基本面数据做出准确的投资判断。
                你的分析报告详实、逻辑严密，能够为投资者提供有力的决策支持。""",
            skills=base_skill,
            tools=[
                GetStockBasicInfoTool(),
            ],
            llm=llm,
        )

    @task
    def base_analysis_task(self) -> Task:
        return Task(
            # config=self.tasks_config["base_analysis_task"],
            # 执行以下步骤：
            #     1. 获取股票的基本信息和财务数据
            #     2. 结合股票所在行业特点，分析公司的盈利能力、成长性、财务稳定性等关键指标
            #     3. 基于分析结果给出投资建议
            description = """
                对{stock_name}（股票代码：{stock_code}）进行基本面分析。
                该股票行业为{industry}\n
                """ + "使用如下skill执行任务：\n" + base_skill[0].instructions,
            expected_output = """
                提供结构化的基本面分析结果，输出json格式：
                {
                    "stock_code": "股票代码",
                    "stock_name": "股票名称",
                    "recommendation": "操作建议(buy/sell/hold)",
                    "confidence": "置信度（0-1）",
                    "reason": "总结原因分析"
                }
                """,
            agent=self.base_analyzer(),
            # output_json=AnalysisResult
        )

    @crew
    def crew(self) -> Crew:
        """创建并返回基本面分析Crew"""
        return Crew(
            agents=[self.base_analyzer()], 
            tasks=[self.base_analysis_task()], 
            skills=base_skill,
            verbose=True
        )

@CrewBase
class SentimentAnalysisCrew:
    """市场情绪分析Crew"""
    # agents_config = "config/agents.yaml"
    # tasks_config = "config/tasks.yaml"

    @agent
    def sentiment_analyzer(self) -> Agent:
        return Agent(
            # config=self.agents_config["sentiment_analyzer"],  
            role="股票市场情绪分析专家",
            goal="""
                深入分析市场情绪、新闻报道、社交媒体等信息，评估市场对股票的看法，提供基于市场情绪的投资决策""",
            backstory="""
                你是一位市场情绪分析专家，拥有丰富的市场心态研究经验。
                你能够敏锐地捕捉市场情绪的变化，分析新闻热点对股票的影响，
                理解市场参与者的情绪波动如何影响股票价格，并据此提供投资指导。""",
            skills=senti_skill,
            tools=[
                GetMarketSentimentTool(),
            ],
            llm=llm
        )

    @task
    def sentiment_analysis_task(self) -> Task:
        return Task(
            # config=self.tasks_config["sentiment_analysis_task"], 
            # 执行以下步骤：
            #     1. 收集与该股票相关的最新新闻和信息
            #     2. 分析市场参与者对该股票的看法和态度
            #     3. 评估社交媒体、论坛等渠道的讨论热度和情感倾向
            #     4. 基于市场情绪给出投资建议
            description="""
                对{stock_name}（股票代码：{stock_code}）进行市场情绪分析。
                该股票行业为{industry}\n""" + "使用如下skill执行任务：\n" + senti_skill[0].instructions,
            expected_output = """
                提供结构化的市场情绪分析结果，输出json格式：
                {
                    "stock_code": "股票代码",
                    "stock_name": "股票名称",
                    "recommendation": "操作建议(buy/sell/hold)",
                    "confidence": "置信度（0-1）",
                    "reason": "总结原因分析"
                }
                """,
            agent=self.sentiment_analyzer(),
            # output_json=AnalysisResult
        )

    @crew
    def crew(self) -> Crew:
        """创建并返回市场情绪分析Crew"""
        return Crew(
            agents=[self.sentiment_analyzer()],
            tasks=[self.sentiment_analysis_task()],
            process=Process.sequential,
            skills=tech_skill,
            verbose=True,
        )
    
@CrewBase
class TechnicalAnalysisCrew:
    """技术面分析Crew"""
    # agents_config = "config/agents.yaml"
    # tasks_config = "config/tasks.yaml"

    @agent
    def technical_analyzer(self) -> Agent:
        return Agent(
            # config=self.agents_config["technical_analyzer"], 
            role="""股票技术面分析专家""",
            goal="""
                通过分析股票的价格走势、技术指标等信息，识别市场趋势和买卖信号，提供基于技术面的投资建议""",
            backstory="""
                你是一位经验丰富的技术面分析师，专精于技术分析领域。
                你能够精确解读K线形态、移动平均线、RSI、MACD等各类技术指标，
                并能根据这些指标的组合变化预测股票短期走势，为投资者把握交易机会。""",
            skills=senti_skill,
            tools=[
                GetStockTechnicalIndicatorsTool(),
            ],
            llm=llm,
        )

    @task
    def technical_analysis_task(self) -> Task:
        return Task(
            # config=self.tasks_config["technical_analysis_task"],
            # 执行以下步骤：
            #     1. 获取股票技术面指标
            #     2. 分析技术指标
            #     3. 基于分析结果给出投资建议
            description="""
                对{stock_name}（股票代码：{stock_code}）进行技术面分析。
                该股票行业为{industry}\n
                """ + "使用如下skill执行任务：\n" + tech_skill[0].instructions,
            expected_output = """
                提供结构化的技术面分析结果，输出json格式：
                {
                    "stock_code": "股票代码",
                    "stock_name": "股票名称",
                    "recommendation": "操作建议(buy/sell/hold)",
                    "confidence": "置信度（0-1）",
                    "reason": "总结原因分析"
                }
                """,
            agent=self.technical_analyzer(),
            # output_json=AnalysisResult
        )

    @crew
    def crew(self) -> Crew:
        """创建并返回技术面分析Crew"""
        return Crew(
            agents=[self.technical_analyzer()],
            tasks=[self.technical_analysis_task()],
            process=Process.sequential,
            skills=tech_skill,
            verbose=True,
        )

if __name__ == "__main__":
   crew = BaseAnalysisCrew()
   print(crew)