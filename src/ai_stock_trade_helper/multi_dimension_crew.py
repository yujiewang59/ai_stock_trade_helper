"""多维分析Crew"""
from pathlib import Path

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
import os

from ai_stock_trade_helper.tools.stock_tools import GetMarketSentimentTool, GetStockBasicInfoTool, GetStockTechnicalIndicatorsTool

from crewai.skills import discover_skills, activate_skill

load_dotenv()

skill_path = "src/ai_stock_trade_helper/skills"
skills = discover_skills(Path(skill_path))

base_skill = [activate_skill(s) for s in skills if s.name == "base-analysis"]
senti_skill = [activate_skill(s) for s in skills if s.name == "sentiment-analysis"]
tech_skill = [activate_skill(s) for s in skills if s.name == "technical-analysis"]

@CrewBase
class BaseAnalysisCrew:
    """基本面分析Crew"""
    llm = LLM(
        model="deepseek/deepseek-reasoner", # openai、deepseek/deepseek-reasoner
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0.1,
        response_format={
            'type': 'json_object'
        },
        max_tokens=4096
    )

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
            # tools=[
            #     GetStockBasicInfoTool(),
            # ],
            llm=self.llm,
        )

    @task
    def base_analysis_task(self) -> Task:
        """生成基本面分析训练数据任务"""
        return Task(
            description="""
                对{stock_name}（股票代码：{stock_code}）进行基本面分析。
                该股票行业为{industry}
                基本面指标为{basic_info}
                """,
            expected_output="""
                提供结构化的基本面分析结果，输出json格式：
                {
                    "stock_code": "股票代码",
                    "stock_name": "股票名称",
                    "reason": "总结原因分析"
                }
                """,
            agent=self.base_analyzer(),
        )

    @crew
    def crew(self) -> Crew:
        """创建并返回基本面分析Crew"""
        return Crew(
            agents=[self.base_analyzer()], 
            tasks=[self.base_analysis_task()], 
            skills=base_skill,
            tracing=True,
            verbose=True
        )

@CrewBase
class SentimentAnalysisCrew:
    """市场情绪分析Crew"""
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

    @agent
    def sentiment_analyzer(self) -> Agent:
        return Agent(
            role="股票市场情绪分析专家",
            goal="""
                深入分析市场情绪、新闻报道、社交媒体等信息，评估市场对股票的看法，提供基于市场情绪的投资决策""",
            backstory="""
                你是一位市场情绪分析专家，拥有丰富的市场心态研究经验。
                你能够敏锐地捕捉市场情绪的变化，分析新闻热点对股票的影响，
                理解市场参与者的情绪波动如何影响股票价格，并据此提供投资指导。""",
            # tools=[
            #     GetMarketSentimentTool(),
            # ],
            llm=self.llm
        )

    @task
    def sentiment_analysis_task(self) -> Task:
        """生成市场情绪分析训练数据任务"""
        return Task(
            description="""
                对{stock_name}（股票代码：{stock_code}）进行市场情绪分析。
                该股票行业为{industry}
                市场情绪数据为
                {sentiment_info}
                """,
            expected_output="""
                提供结构化的市场情绪分析结果，输出json格式：
                {
                    "stock_code": "股票代码",
                    "stock_name": "股票名称",
                    "reason": "总结原因分析"
                }
                """,
            agent=self.sentiment_analyzer(),
        )

    @crew
    def crew(self) -> Crew:
        """创建并返回市场情绪分析Crew"""
        return Crew(
            agents=[self.sentiment_analyzer()],
            tasks=[self.sentiment_analysis_task()],
            process=Process.sequential,
            skills=senti_skill,
            tracing=True,
            verbose=True,
        )
    
@CrewBase
class TechnicalAnalysisCrew:
    """技术面分析Crew"""
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
            # tools=[
            #     GetStockTechnicalIndicatorsTool(),
            # ],
            llm=self.llm,
        )

    @task
    def technical_analysis_task(self) -> Task:
        """生成技术面分析训练数据任务"""
        return Task(
            description="""
                对{stock_name}（股票代码：{stock_code}）进行技术面分析。
                该股票行业为{industry}
                技术面指标数据为
                {technical_info}
                """,
            expected_output="""
                提供结构化的技术面分析结果，输出json格式：
                {
                    "stock_code": "股票代码",
                    "stock_name": "股票名称",
                    "reason": "总结原因分析"
                }
                """,
            agent=self.technical_analyzer(),
        )

    @crew
    def crew(self) -> Crew:
        """创建并返回技术面分析Crew"""
        return Crew(
            agents=[self.technical_analyzer()],
            tasks=[self.technical_analysis_task()],
            process=Process.sequential,
            skills=tech_skill,
            tracing=True,
            verbose=True,
        )

if __name__ == "__main__":
   crew = BaseAnalysisCrew()
   print(crew)