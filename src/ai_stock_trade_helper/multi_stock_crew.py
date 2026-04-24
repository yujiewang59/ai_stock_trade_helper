"""多股分析Crew"""
from pathlib import Path

from crewai import Agent, Crew, Process, Task,LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv
import os
from crewai.skills import discover_skills, activate_skill

from ai_stock_trade_helper.models import MultiStockDecision

load_dotenv()

# 初始化 DeepSeek 模型
llm = LLM(
    model="deepseek/deepseek-reasoner" \
    "", # 注意此处需带 openai/ 前缀以触发兼容模式
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_BASE"),
    temperature=0.01,
    response_format={
        'type': 'json_object'
    },
    max_tokens=4096
)

skills = discover_skills(Path("skills"))
activated = [activate_skill(s) for s in skills if s.name == "multi-stock-analysis"]

@CrewBase
class MultiStockCrew:
    """多股分析Crew - 通过行业投资分析智能体综合多支股票的决策"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def multi_stock_analyzer(self) -> Agent:
        return Agent(
            # config=self.agents_config["multi_stock_analyzer"],  # type: ignore[index]
            role="""股票投资分析专家""",
            goal="""根据多支股票的投资决策结果，结合当前收益情况、风险偏好、行业特点，生成行业级别的综合投资策略""",
            backstory="""
                你是一位顶级的行业投资分析师，拥有丰富的投资组合管理经验。
                你能够从宏观到微观分析行业趋势，对比不同股票的相对优劣，
                制定平衡风险与收益的投资策略，实现投资组合的最优配置。""",
            skills=activated,
            llm=llm,
            # verbose=True,
        )


    @task
    def multi_stock_analysis_task(self) -> Task:
        return Task(
            # config=self.tasks_config["multi_stock_analysis_task"],  # type: ignore[index]
            # 执行以下步骤：
            #     1. 总结所有股票的投资决策结果，做出决策的原因，
            #     2. 分析股票间的相关性和行业趋势
            #     3. 评估当前的用户总资产和持仓情况
            #     4. 考虑组合风险平衡问题
            #     5. 生成每支股票的最终决策、分析原因总结、投资策略和建议
            description="""
                结合用户输入的当前持仓、风险偏好、行业特点对以下多支股票的投资决策进行综合分析，生成行业级别的投资策略。
                当前行业为{industry}，用户风险偏好为{risk_level}
                
                所有股票列表和决策信息：
                {multi_stock_decisions}

                用户总资产：{user_assets}

                用户当前持仓情况：
                {user_stock_holds}\n
                """ + "使用如下skill执行任务：\n" + activated[0].instructions,
            expected_output = """
                提供结构化的多股综合决策结果，输出json格式：
                {
                    "decisions": [
                        {
                            "stock_code": "股票代码1",
                            "stock_name": "股票名称1",
                            "confidence": "综合置信度（0-1）",
                            "recommendation": "操作建议(buy/sell/hold)",
                            "position_size": "建议仓位大小（0-1）"
                        },
                        {
                            "stock_code": "股票代码2",
                            "stock_name": "股票名称2",
                            "confidence": "综合置信度（0-1）",
                            "recommendation": "操作建议(buy/sell/hold)",
                            "position_size": "建议仓位大小（0-1）"
                        }
                    ],
                    "summary": "总结每支股票的综合分析报告（数据支撑）、综合决策原因分析、风险评估",
                    "overall_recommendation": "综合性的行业投资建议"
                }
                """,
            agent=self.multi_stock_analyzer(),
            # output_json=MultiStockDecision
        )

    @crew
    def crew(self) -> Crew:
        """创建并返回多股分析Crew"""
        return Crew(
            agents=[self.multi_stock_analyzer()],
            tasks=[self.multi_stock_analysis_task()],
            process=Process.sequential,
            skills=activated,
            verbose=True,
        )
