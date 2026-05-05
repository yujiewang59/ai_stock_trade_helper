"""多维分析Crew"""
import json
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
        model="openai", 
        api_key="0",
        base_url="http://localhost:8000/v1",
        temperature=0.3,
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
            # skills=base_skill,
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
                提供结构化的市场情绪分析结果，输出json格式：
                {
                    "stock_code": "股票代码",
                    "stock_name": "股票名称",
                    "reason": "总结分析"
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
            # skills=base_skill,
            verbose=True
        )

if __name__ == "__main__":
   inputs = {
       "stock_code": "sz300001",
       "stock_name": "特锐德",
       "industry": "酒店旅游（消费行业）",
       "basic_info": json.dumps({
            "净资产收益率(ROE)": 0.84,
            "销售净利率": 2.643447,
            "毛利率": 23.046667,
            "总资产报酬率(ROA)": 0.288548,
            "营业总收入增长率": 5.409063,
            "基本每股收益": 0.07,
            "流动比率": 1.201959,
            "资产负债率": 60.369526,
            "每股现金流": -0.870429,
            "市盈率": 531.5796901217694,
            "市销率": 14.05203095440139
       }, ensure_ascii=False, indent=2)
   }

   base_results = BaseAnalysisCrew().crew().kickoff(inputs=inputs)
   print(base_results.raw)