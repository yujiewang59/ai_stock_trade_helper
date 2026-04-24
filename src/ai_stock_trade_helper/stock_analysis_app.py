import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from ai_stock_trade_helper.util import industyInfo


# 后端FastAPI服务的基础地址
API_BASE_URL = "http://localhost:8000"
# 分析任务启动接口
ANALYSIS_START_ENDPOINT = f"{API_BASE_URL}/analysis/start"
# 任务状态查询接口
TASK_STATUS_ENDPOINT = f"{API_BASE_URL}/status/{{task_id}}"

# 行业列表，你可以根据业务需求自行增删修改
INDUSTRIES = industyInfo.industry_info
# ==========================================================================

def reset_task_state():
    """重置任务状态，当用户修改输入参数时自动调用，清空旧的分析结果"""
    st.session_state.task_id = None
    st.session_state.task_status = None
    st.session_state.analysis_result = None

# 初始化Session State，保存页面状态，避免刷新丢失
if 'user_holds' not in st.session_state:
    st.session_state.user_holds = None  # 保存用户持仓数据

if 'task_id' not in st.session_state:
    st.session_state.task_id = None

if 'task_status' not in st.session_state:
    st.session_state.task_status = None

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# 页面基础配置
st.set_page_config(
    page_title="行业级股票分析决策AI",
    page_icon="📈",
    layout="wide"
)

# 页面标题
st.title("📈 行业级股票分析决策AI应用")

# ====================== 1. 行业选择 ======================
st.subheader("🏭 行业选择")
selected_industry = st.selectbox(
    "请选择需要分析的行业",
    options=INDUSTRIES,
    format_func=lambda x: x["industry"],
    on_change=reset_task_state
)
# 选中的行业完整字典，赋值给行业信息变量，符合需求
industry_info = selected_industry

# ====================== 2. 资产信息输入 ======================
st.subheader("💰 您的总资产信息")
total_asset = st.number_input(
    "总可用资产（元，必选）",
    min_value=0.0,
    step=100.0,
    format="%.2f",
    help="你当前在该行业的总可用投资资金",
    on_change=reset_task_state
)

# ====================== 3. 持仓信息输入 ======================
st.subheader("📊 行业内股票持仓情况（可选）")
st.markdown("你可以填写当前持有的该行业股票信息，点击表格下方的「+」按钮新增行，填写完成后点击「完成持仓填写」保存数据。")

# 初始化持仓表格数据
if st.session_state.user_holds is None:
    init_df = pd.DataFrame(columns=["股票代码", "持股数量", "当前价格"])
else:
    init_df = st.session_state.user_holds

# 可编辑动态表格，支持用户自行增删行
edited_df = st.data_editor(
    init_df,
    use_container_width=True,
    num_rows="dynamic",  # 开启动态增删行功能
    column_config={
        "股票代码": st.column_config.TextColumn(
            "股票代码",
            help="股票的交易代码，例如：600036",
            max_chars=10,
        ),
        "持股数量": st.column_config.NumberColumn(
            "持股数量",
            help="你持有的该股票的股数",
            min_value=0.0,
            step=1.0,
            format="%.0f",
        ),
        "当前价格": st.column_config.NumberColumn(
            "当前价格",
            help="该股票的当前价格（留空则系统自动获取）",
            min_value=0.0,
            step=0.01,
            format="%.2f",
        ),
    },
    key="hold_editor"
)

# 完成持仓填写按钮
if st.button("✅ 完成持仓填写", on_click=reset_task_state):
    # 过滤空行，只保存有效数据
    valid_rows = edited_df.dropna(how="all")
    st.session_state.user_holds = valid_rows
    st.success(f"持仓信息已保存，共 {len(valid_rows)} 条持仓记录")

# 展示已保存的持仓信息
if st.session_state.user_holds is not None and len(st.session_state.user_holds) > 0:
    st.write("已保存的持仓：")
    st.dataframe(st.session_state.user_holds, use_container_width=True, hide_index=True)

# ====================== 4. 风险偏好选择 ======================
st.subheader("⚖️ 投资风险偏好（可选）")
risk_options = {
    "稳健": "low",
    "均衡": "medium",
    "激进": "high"
}
risk_choice = st.radio(
    "请选择你的风险偏好",
    options=list(risk_options.keys()),
    index=1,  # 默认选中中风险
    horizontal=True,
    on_change=reset_task_state
)
risk_level = risk_options[risk_choice]

st.markdown("---")

# ====================== 分析按钮与状态控制 ======================
# 验证必选字段是否填写完成
is_input_valid = (
    industry_info is not None 
    and total_asset > 0.0
)

# 开始分析按钮，必选字段未填时自动禁用
analyze_button = st.button(
    "🚀 开始分析",
    disabled=not is_input_valid,
    type="primary",
    use_container_width=True
)

# 处理分析按钮点击事件
if analyze_button and is_input_valid:
    # 整理持仓数据
    holdings = []
    if st.session_state.user_holds is not None and len(st.session_state.user_holds) > 0:
        for _, row in st.session_state.user_holds.iterrows():
            holdings.append({
                "symbol": row["股票代码"],
                "shares": row["持股数量"],
                "current_price": row["当前价格"] if pd.notna(row["当前价格"]) else None
            })
    
    # 构造请求体，完全匹配后端接口要求
    request_data = {
        "industry": industry_info['industry'],
        "industry_label": industry_info['industry_label'],
        "user_assets": total_asset,
        "user_stock_holds": holdings,
        "risk_level": risk_level
    }
    
    try:
        # 发送POST请求启动分析任务
        response = requests.post(
            ANALYSIS_START_ENDPOINT,
            json=request_data,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        # 获取任务ID，进入轮询状态
        task_id = result.get("task_id")
        if task_id:
            st.session_state.task_id = task_id
            st.session_state.task_status = "pending"
            st.success("分析任务启动！")
            # 触发页面重跑，进入轮询逻辑
            st.rerun()
        else:
            st.error("启动分析任务失败，未获取到任务ID")
    except Exception as e:
        st.error(f"启动分析任务失败：{str(e)}")

# ====================== 任务状态轮询 ======================
if st.session_state.task_id is not None and st.session_state.task_status == "pending":
    # 加载占位符
    status_placeholder = st.empty()
    status_placeholder.info("🤖 智能体正在分析中，请稍候...")
    
    try:
        # 查询任务状态
        url = TASK_STATUS_ENDPOINT.format(task_id=st.session_state.task_id)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        task_result = response.json()
        
        status = task_result.get("status")
        if status == "completed":
            # 任务完成，保存结果
            st.session_state.task_status = "completed"
            st.session_state.analysis_result = task_result.get("result")
            status_placeholder.empty()
            st.rerun()
        elif status == "failed":
            # 任务失败，展示错误
            st.session_state.task_status = "failed"
            error_msg = task_result.get("error", "未知错误")
            status_placeholder.error(f"任务失败！错误：{error_msg}")
        else:
            # 任务处理中，等待2秒后重查
            time.sleep(2)
            st.rerun()
    except Exception as e:
        st.error(f"查询任务状态失败：{str(e)}")
        time.sleep(2)
        st.rerun()

# ====================== 分析结果渲染 ======================
if st.session_state.analysis_result is not None:
    st.markdown("---")
    st.subheader("📋 分析结果")
    
    result = st.session_state.analysis_result
    
    # 1. 分析时间
    analysis_time = result.get("analysis_timestamp")
    if analysis_time:
        try:
            if isinstance(analysis_time, str):
                analysis_time = datetime.fromisoformat(analysis_time.replace('Z', '+00:00'))
            st.caption(f"分析时间：{analysis_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            st.caption(f"分析时间：{analysis_time}")
    
    st.markdown("---")
    
    # 2. 个股投资决策表格
    st.subheader("💡 个股投资决策")
    decisions = result.get("decisions", [])
    if decisions:
        decision_data = []
        # 操作建议映射，转为中文更友好
        rec_map = {
            "buy": "买入",
            "sell": "卖出",
            "hold": "持有"
        }
        
        for d in decisions:
            rec = rec_map.get(d.get("recommendation"), d.get("recommendation"))
            # 置信度转百分比展示
            confidence = f"{d.get('confidence', 0)*100:.1f}%"
            # 仓位占比转百分比展示
            position = f"{d.get('position_size', 0)*100:.1f}%" if d.get("position_size") else "-"
            decision_data.append({
                "股票代码": d.get("stock_code"),
                "股票名称": d.get("stock_name"),
                "操作建议": rec,
                "置信度": confidence,
                "建议仓位占比": position
            })
        
        decision_df = pd.DataFrame(decision_data)
        st.dataframe(
            decision_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无个股决策数据")
    
    st.markdown("""
            <style>
            /* 强制覆盖 Streamlit 的 disabled textarea 样式 */
            div[data-testid="stTextArea"] textarea:disabled {
                background-color: #ffffff !important;
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important; /* 关键：解决 Chrome 灰字 */
                opacity: 1 !important;
            }

            /* 可选：去掉边框灰显 */
            div[data-testid="stTextArea"] textarea:disabled {
                border-color: #d0d0d0 !important;
            }
            </style>
            """, 
            unsafe_allow_html=True
            )
    
    # 3. 综合分析总结
    st.subheader("📝 综合分析总结")
    summary = result.get("summary", "暂无总结")
    st.text_area(
        "",
        value=summary,
        disabled=True,
        height=150,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # 4. 整体投资建议
    st.subheader("🎯 整体投资建议")
    overall_rec = result.get("overall_recommendation", "暂无建议")
    st.text_area(
        "",
        value=overall_rec,
        disabled=True,
        height=100,
        label_visibility="collapsed"
    )