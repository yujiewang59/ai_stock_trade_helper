# 📈 AI Stock Trade Helper

> **基于 CrewAI 的多智能体股票分析决策系统** — 融合基本面、技术面、市场情绪三维分析，提供行业级投资组合建议。

[![Python Version](https://img.shields.io/badge/python-3.10--3.14-blue)](pyproject.toml)
[![CrewAI](https://img.shields.io/badge/crewAI-1.14.2-orange)](https://crewai.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🌟 功能概览

| 特性 | 说明 |
|------|------|
| **三维度分析** | 基本面、技术面、市场情绪 — 每维度由独立 AI 智能体执行 |
| **并行加速** | 多只股票的三维分析完全并行执行，大幅缩短分析时间 |
| **行业智能筛选** | 基于财务指标自动筛选行业内优质股票（ROE、净利率、负债率等） |
| **综合分析** | 基于行业特性的差异化权重，综合三维度结果生成单股决策 |
| **组合优化** | 结合用户持仓、风险偏好，校准单股决策并优化投资组合 |
| **Streamlit UI** | 交互式 Web 界面，方便输入和查看结果 |
| **FastAPI 后端** | 异步任务管理，支持批量分析请求 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit 前端 (UI)                     │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP / REST
┌─────────────────────────▼───────────────────────────────┐
│                FastAPI 后端 (任务调度)                     │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    CrewAI Flow 编排                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. Setup Stage: 行业筛选 + 股票选择 / 用户持仓合并    │  │
│  └──────────────────────┬─────────────────────────────┘  │
│  ┌──────────────────────▼─────────────────────────────┐  │
│  │  2. Parallel Analysis Stage (并行执行)               │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │  │
│  │  │ 基本面分析   │  │ 技术面分析    │  │ 市场情绪   │  │  │
│  │  │ (DeepSeek)  │  │ (DeepSeek)   │  │ 分析       │  │  │
│  │  │ + akShare   │  │ + tushare    │  │ (DeepSeek) │  │  │
│  │  └──────┬──────┘  └──────┬───────┘  │ + 新浪新闻 │  │  │
│  │         │                │          └──────┬──────┘  │  │
│  │         └────────────────┼─────────────────┘         │  │
│  └──────────────────────────▼───────────────────────────┘  │
│  ┌──────────────────────────▼───────────────────────────┐  │
│  │  3. Synthesis Stage: 综合分析 (三维度融合决策)          │  │
│  └──────────────────────────┬───────────────────────────┘  │
│  ┌──────────────────────────▼───────────────────────────┐  │
│  │  4. Multi-Stock Stage: 组合优化与投资建议生成           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 智能体（Agent）说明

本系统共包含 **5 个专业 AI 智能体**，每者专注于不同的分析维度：

### 1. 基本面分析专家 (`BaseAnalysisCrew`)
- **角色**: 股票基本面分析专家
- **工具**: `GetStockBasicInfoTool`（基于 akShare）
- **能力**: 分析 ROE、净利率、毛利率、资产负债率、市盈率等财务指标
- **Skill**: `base-analysis` — 含行业差异化权重（消费/科技/医药/周期等 8 大行业）

### 2. 技术面分析专家 (`TechnicalAnalysisCrew`)
- **角色**: 股票技术面分析专家
- **工具**: `GetStockTechnicalIndicatorsTool`（基于 tushare）
- **能力**: 计算 ADX、RSI、MACD、布林带、动量、波动率、赫斯特指数等
- **Skill**: `technical-analysis` — 5 大技术维度（趋势/均值回归/动量/波动率/统计套利）

### 3. 市场情绪分析专家 (`SentimentAnalysisCrew`)
- **角色**: 股票市场情绪分析专家
- **工具**: `GetMarketSentimentTool`（抓取新浪财经新闻）
- **能力**: 分析新闻舆论情感倾向、社交媒体热度
- **Skill**: `sentiment-analysis` — 含行业差异化权重

### 4. 投资决策管理专家 (`SynthesisCrew`)
- **角色**: 综合分析决策者
- **能力**: 融合三维度结果，按行业权重加权计算综合得分
- **Skill**: `synthesis-analysis` — 置信度加权融合、风险偏好阈值调整

### 5. 行业投资分析专家 (`MultiStockCrew`)
- **角色**: 投资组合优化师
- **能力**: 结合用户持仓、资产、风险偏好，校准单股决策并给出组合建议
- **Skill**: `multi-stock-analysis` — 仓位超配检测、分散度优化

---

## 📋 工作流程 (Flow)

```
┌─────────────────────────────────────────────────────────────┐
│                    StockAnalysisFlow                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  @start() setup_analysis                                    │
│    ├─ 行业筛选 → 财务指标过滤 → 合并用户持仓 → StockInfo[]  │
│    └─ 并行触发下三个阶段                                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ @listen() base_analysis_stage  (基本面分析 - 并行)    │    │
│  │ @listen() technical_analysis_stage (技术面 - 并行)    │    │
│  │ @listen() sentiment_analysis_stage (情绪分析 - 并行)  │    │
│  └───────────────┬──────────────────────────────┬───────┘    │
│                  └──────────┬───────────────────┘            │
│                             │  and_() 等待全部完成            │
│  @listen(and_(...)) synthesis_analysis                       │
│    ├─ 按股票配对各维度结果                                    │
│    ├─ 置信度加权融合 → 综合决策                               │
│    └─ 触发多股分析                                            │
│                                                             │
│  @listen() multi_stock_analysis                             │
│    ├─ 仓位超配检测                                           │
│    ├─ 风险偏好适配                                           │
│    └─ 最终投资组合建议                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 前置要求

- Python >= 3.10, < 3.14
- [uv](https://docs.astral.sh/uv/) 包管理工具

### 1. 安装

```bash
# 安装 uv（如未安装）
pip install uv

# 克隆项目后，安装依赖
cd ai-stock-trade-helper
uv sync
```

### 2. 配置环境变量

复制 `env.example` 为 `.env` 并填入你的 API 密钥：

```bash
cp env.example .env
```

```ini
# .env
DEEPSEEK_API_KEY="your_deepseek_api_key_here"
DEEPSEEK_API_BASE="https://api.deepseek.com"
TUSHARE_TOKEN="your_tushare_token_here"
```

> **注意**: 本系统默认使用 **DeepSeek Reasoner** 作为 LLM。如需切换其他模型，修改 `multi_dimension_crew.py`、`multi_stock_crew.py`、`synthesis_crew.py` 中的 `LLM` 配置。

### 3. 运行

#### 方式一：Streamlit Web 界面（推荐）

```bash
# 启动 FastAPI 后端（终端 1）
uvicorn ai_stock_trade_helper.backend:app --reload --port 8000

# 启动 Streamlit 前端（终端 2）
uv run streamlit run src/ai_stock_trade_helper/stock_analysis_app.py
```

打开浏览器访问 `http://localhost:8501`

#### 方式二：命令行直接运行

```bash
crewai run
```

---

## 🖥️ 界面截图与使用指南

### Streamlit 界面操作步骤

1. **选择行业** — 从下拉菜单选择待分析的行业（如：半导体、银行、医药等）
2. **输入资产** — 填写当前总可用投资资金
3. **填写持仓（可选）** — 动态表格添加当前持有的行业内股票
4. **选择风险偏好** — 稳健 / 均衡 / 激进
5. **点击「开始分析」** — 系统自动执行完整分析流程
<img width="2464" height="1060" alt="截屏2026-04-24 16 34 51" src="https://github.com/user-attachments/assets/4f62a98c-9f02-40a2-b545-8cb581078a12" />


### 结果展示

- **个股投资决策表** — 每只股票的买入/卖出/持有建议、置信度、建议仓位
- **综合分析总结** — 当前组合概况、详细原因分析、整体风险评估
- **整体投资建议** — 行业级别的加减仓建议与配置策略
<img width="2434" height="959" alt="截屏2026-04-24 16 51 48" src="https://github.com/user-attachments/assets/21b8da29-e5a0-42e2-992d-bd2e6f8bbb89" />


---

## 🔧 核心技术栈

| 类别 | 技术 |
|------|------|
| **AI 框架** | [CrewAI](https://crewai.com) v1.14.2（多智能体编排） |
| **大语言模型** | DeepSeek Reasoner（通过 LiteLLM 兼容接口） |
| **技术指标计算** | 自定义 Python 实现（EMA、ADX、RSI、布林带、Hurst 指数等） |
| **数据源** | [akShare](https://akshare.akfamily.xyz/)（基本面+行业成分股）、[tushare](https://tushare.pro/)（日K线数据）、新浪财经（新闻舆情） |
| **后端框架** | FastAPI（异步任务调度） |
| **前端框架** | Streamlit（交互式数据面板） |
| **状态管理** | CrewAI Flow（Pydantic State + 异步编排） |
| **包管理** | uv（基于 Rust 的 Python 包管理器） |

---

## 📁 项目结构

```
ai-stock-trade-helper/
├── src/ai_stock_trade_helper/
│   ├── __init__.py                 # 包入口
│   ├── models.py                   # Pydantic 数据模型
│   ├── flow.py                     # CrewAI Flow 编排（核心工作流）
│   ├── backend.py                  # FastAPI 异步后端
│   ├── stock_analysis_app.py       # Streamlit 前端界面
│   ├── multi_dimension_crew.py     # 基本面/技术面/情绪 Crew 定义
│   ├── multi_stock_crew.py         # 多股分析 Crew 定义
│   ├── synthesis_crew.py           # 综合分析 Crew 定义
│   ├── config/
│   │   ├── agents.yaml             # 智能体配置（已注释，改用代码内定义）
│   │   └── tasks.yaml              # 任务配置（已注释，改用代码内定义）
│   ├── skills/
│   │   ├── base-analysis/SKILL.md              # 基本面分析 Skill
│   │   ├── technical-analysis/SKILL.md         # 技术面分析 Skill
│   │   ├── sentiment-analysis/SKILL.md         # 市场情绪分析 Skill
│   │   ├── synthesis-analysis/SKILL.md         # 综合分析 Skill
│   │   └── multi-stock-analysis/SKILL.md       # 多股分析 Skill
│   ├── tools/
│   │   ├── stock_tools.py         # 股票数据获取工具
│   │   └── screen_stocks.py       # 行业股票筛选工具
│   └── util/
│       ├── caculate_func.py       # 技术指标计算函数
│       └── industyInfo.py         # 行业信息映射
├── .env                            # 环境变量（API 密钥）
├── pyproject.toml                  # 项目配置与依赖
├── requirements.txt                # 依赖清单
└── uv.lock                         # 依赖锁定文件
```

---

## ⚙️ 配置详解

### 行业覆盖

系统支持 **50 个** A 股行业板块的分析，涵盖：

- **科技类**: 电子器件、电子信息、发电设备、飞机制造、仪器仪表
- **金融类**: 金融行业、房地产
- **消费类**: 酿酒行业、家电行业、纺织行业、服装鞋类、食品行业
- **医药类**: 生物制药、医疗器械
- **周期类**: 钢铁行业、有色金属、化工行业、煤炭行业、石油行业
- **公用事业**: 电力行业、供水供气、环保行业
- **其他**: 船舶制造、传媒娱乐、交通运输、建筑建材、商业百货等

完整列表见 `src/ai_stock_trade_helper/util/industyInfo.py`

### 股票筛选条件

| 指标 | 默认阈值 | 说明 |
|------|---------|------|
| 流通市值 | ≥ 30 亿元 | 排除小盘股流动性风险 |
| ROE | ≥ 8% | 盈利能力门槛 |
| 销售净利率 | ≥ 3% | 盈利质量要求 |
| 资产负债率 | ≤ 70% | 财务安全边界 |
| 扣非净利润 | > 0 | 排除亏损股 |
| 经营现金流 | > 0 | 现金流健康 |
| 营收/利润增长率 | ≥ 0 | 成长性要求 |

### 风险偏好与仓位控制

| 风险偏好 | 单股最大仓位 | 最低分散要求 |
|---------|-------------|-------------|
| 稳健 (low) | 20% | 至少 5 只 |
| 均衡 (medium) | 30% | 至少 3 只 |
| 激进 (high) | 40% | 至少 2 只 |

---

## 📊 分析维度与权重

### 综合分析（三维度融合）

不同行业的三维度权重（源自 `synthesis-analysis` Skill）：

| 行业类型 | 基本面 | 技术面 | 情绪面 |
|---------|-------|-------|-------|
| 消费 | 50% | 35% | 15% |
| 科技 | 30% | 35% | 35% |
| 医药 | 40% | 30% | 30% |
| 周期 | 40% | 40% | 20% |
| 金融 | 55% | 30% | 15% |
| 房地产 | 45% | 30% | 25% |
| 公用事业 | 60% | 30% | 10% |
| 通用 | 40% | 35% | 25% |

### 决策阈值（受风险偏好影响）

| 风险偏好 | 买入阈值 (buy) | 持有区间 (hold) | 卖出阈值 (sell) |
|---------|--------------|----------------|---------------|
| 低风险 | ≥ 0.75 | 0.45 ~ 0.75 | < 0.45 |
| 中风险 | ≥ 0.70 | 0.40 ~ 0.70 | < 0.40 |
| 高风险 | ≥ 0.65 | 0.35 ~ 0.65 | < 0.35 |

---

### 添加新 Skill

在 `src/ai_stock_trade_helper/skills/` 下创建新目录和 `SKILL.md` 文件，然后在 Crew 中引用：

```python
from crewai.skills import discover_skills, activate_skill

skills = discover_skills(Path("skills"))
my_skill = [activate_skill(s) for s in skills if s.name == "my-skill"]
agent = Agent(..., skills=my_skill)
```

### 切换 LLM 模型

```python
from crewai import LLM

llm = LLM(
    model="openai/gpt-4o",           # 或 "anthropic/claude-sonnet-4-20250514"
    temperature=0.1,
    response_format={"type": "json_object"},
    max_tokens=4096,
)
```

---

## ⚠️ 免责声明

> **本系统生成的所有分析结果仅为投资辅助参考，不构成任何投资建议或操作指导。**
>
> 股票市场有风险，投资需谨慎。本系统不保证任何投资回报，不对因使用本系统所产生的任何投资损失承担责任。所有决策应基于用户自身的独立判断。

---

## 📚 参考资料

技术面指标分析计算参考：https://github.com/LiteObject/ai-stock-analyst

- [CrewAI 文档](https://docs.crewai.com)
- [akShare 文档](https://akshare.akfamily.xyz/)
- [tushare 文档](https://tushare.pro/document)
- [DeepSeek API](https://platform.deepseek.com/)
- [Streamlit 文档](https://docs.streamlit.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

## 📄 License

MIT

---

## 📖 Citation

如果您在学术研究或出版物中使用了本项目，请引用如下：

```bibtex
@misc{ai-stock-trade-helper,
  author = {Your Name},
  title = {AI Stock Trade Helper: Multi-Agent Stock Analysis System powered by CrewAI},
  year = {2025},
  publisher = {GitHub},
  url = {}  % TODO: https://github.com/yujiewang59/ai_stock_trade_helper
}
```
