"""综合分析Crew"""
from pathlib import Path

from crewai import Agent, Crew, Process, Task,LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from dotenv import load_dotenv
import os

from ai_stock_trade_helper.models import AnalysisResult

from crewai.skills import discover_skills, activate_skill

load_dotenv()

# 初始化 DeepSeek 模型
llm = LLM(
    model="deepseek/deepseek-reasoner",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_BASE"),
    temperature=0.05,
    response_format={
        'type': 'json_object'
    },
    max_tokens=4096
)

skill_path = "src/ai_stock_trade_helper/skills"
skills = discover_skills(Path(skill_path))
activated = [activate_skill(s) for s in skills if s.name == "synthesis-analysis"]


@CrewBase
class SynthesisCrew:
    """综合分析Crew - 通过投资决策管理智能体综合三维分析结果"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def investment_decision_manager(self) -> Agent:
        return Agent(
            # config=self.agents_config["investment_decision_manager"],
            role="""股票投资管理专家""",
            goal="""
                综合基本面分析、技术面分析和市场情绪分析的结果，生成全面的投资决策建议""",
            backstory="""
                你是一位资深的投资决策专家，拥有20年的投资管理经验。
                你擅长统筹各类分析结果，权衡不同维度的信息，做出综合而平衡的投资决策。
                你的决策考虑周全、风险管理严格，能够为投资者提供最优的投资方案。""",
            skills=activated,
            llm=llm,
            # verbose=True,
        )

    @task
    def synthesis_task(self) -> Task:
        return Task(
            # config=self.tasks_config["synthesis_task"],
            # 执行以下步骤：
            #     1. 审阅基本面、技术面、市场情绪的分析内容
            #     2. 分析基本面、技术面、市场情绪分析决策是否存在分歧，以及分歧的原因
            #     3. 结合行业特点、用户风险偏好对三个维度的建议进行评分和权重分配
            #     4. 综合考虑各维度的置信度，生成综合评分
            #     5. 基于综合分析结果，给出最终的投资决策
            description="""
                结合基本面、技术面和市场情绪分析结果，综合分析股票 {stock_name}，生成投资决策，分析报告。
                该股票行业为{industry}，用户风险偏好为{risk_level}
                
                三种维度的分析结果：
                {analysis_results}\n
                """ + "使用如下skill执行任务：\n" + activated[0].instructions
                ,
            expected_output = """
                提供结构化的股票综合分析结果，输出json格式：
                {
                    "stock_code": "股票代码",
                    "stock_name": "股票名称",
                    "recommendation": "操作建议(buy/sell/hold)",
                    "confidence": "综合置信度（0-1）",
                    "reason": "综合分析报告:三种维度的分析原因，风险提示（市场风险、个股风险）"
                }
                """,
            agent=self.investment_decision_manager(),
            # output_json=AnalysisResult
        )

    @crew
    def crew(self) -> Crew:
        """创建并返回综合分析Crew"""
        return Crew(
            agents=[self.investment_decision_manager()],
            tasks=[self.synthesis_task()],
            process=Process.sequential,
            skills=activated,
            verbose=True,
        )
