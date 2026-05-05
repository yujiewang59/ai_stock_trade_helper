import json
import random
import pandas as pd
from func_timeout import func_timeout, FunctionTimedOut

import akshare as ak
from ai_stock_trade_helper.util.industyInfo import industry_info
from ai_stock_trade_helper.tools.stock_tools_func import StockBasicInfoTool, StockTechnicalIndicatorsTool, MarketSentimentTool
from ai_stock_trade_helper.FT_data_maker import BaseAnalysisCrew, TechnicalAnalysisCrew, SentimentAnalysisCrew
from ai_stock_trade_helper.tools.screen_stocks import get_stock_base_data

# 基本面分析测试数据构建器
async def base_data_builder(stock_code: str, industry: str) -> tuple[dict, dict]:
    """构建基本面数据的输入输出格式"""
    try:
        base_data: dict = json.loads(StockBasicInfoTool(stock_code))
        stock_name = base_data.get("股票名称", "N/A")
        inputs = {"stock_code": stock_code, "stock_name": stock_name, "industry": industry, "basic_info": base_data['data']}

        raw_result = await BaseAnalysisCrew().crew().akickoff(inputs=inputs)
        base_results = json.loads(raw_result.raw)
        sft_data = base_results["SFT"]
        rlaif_data = base_results["RLAIF"]

        instruction = sft_data.get("instruction", "请根据提供的基本面数据进行分析，给出投资建议。")
        sft_data = {
            "instruction": instruction,
            "input": "",
            "output": sft_data.get("output", {})
        }

        return sft_data, rlaif_data
    except Exception as e:
        print(f"{stock_code}基本面分析数据构建失败: {e}")
        return {}, {}

# 基本面分析测试数据保存器
def base_output_data_saver(sft_data: dict, rlaif_data: dict):
    sft_path = "dataset/base/base_analysis_SFT_test_data.json"
    rlaif_path = "dataset/base/base_analysis_RLAIF_test_data.json"
    if len(sft_data) == 0 or len(rlaif_data) == 0:
        print("基本面分析数据为空，跳过保存")
        return

    """保存生成的基本面分析数据到本地文件"""
    if len(sft_data) > 0:
        with open(sft_path, "a", encoding='utf-8') as f:
            f.write(json.dumps(sft_data, ensure_ascii=False, indent=2)+",")  # 每条数据后添加逗号分隔，保持文件格式正确
            f.write("\n")  # 添加换行符分隔不同条数据

    if len(rlaif_data) > 0:
        with open(rlaif_path, "a", encoding='utf-8') as f:
            f.write(json.dumps(rlaif_data, ensure_ascii=False, indent=2)+",")  # 每条数据后添加逗号分隔，保持文件格式正确
            f.write("\n")  # 添加换行符分隔不同条数据


# 技术面分析测试数据构建器
async def technical_data_builder(stock_code: str, industry: str) -> tuple[dict, dict]:
    """构建技术面数据的输入输出格式"""
    try:
        technical_data: dict = json.loads(StockTechnicalIndicatorsTool(stock_code))
        stock_name = get_stock_base_data(stock_code)['name'].values[0]
        inputs = {"stock_code": stock_code, "stock_name": stock_name, "industry": industry, "technical_info": technical_data}

        raw_result = await TechnicalAnalysisCrew().crew().akickoff(inputs=inputs)
        technical_results = json.loads(raw_result.raw)
        sft_data = technical_results["SFT"]
        rlaif_data = technical_results["RLAIF"]

        instruction = sft_data.get("instruction", "请根据提供的基本面数据进行分析，给出投资建议。")
        sft_data = {
            "instruction": instruction,
            "input": "",
            "output": sft_data.get("output", {})
        }

        return sft_data, rlaif_data
    except Exception as e:
        print(f"{stock_code}技术面分析数据构建失败: {e}")
        return {}, {}



# 技术面分析测试数据保存器
def technical_output_data_saver(sft_data: dict, rlaif_data: dict):
    """保存生成的技术面分析数据到本地文件"""
    sft_path = "dataset/tech/technical_analysis_SFT_test_data.json"
    rlaif_path = "dataset/tech/technical_analysis_RLAIF_test_data.json"

    if len(sft_data) > 0:
        with open(sft_path, "a", encoding='utf-8') as f:
            f.write(json.dumps(sft_data, ensure_ascii=False, indent=2)+",")  # 每条数据后添加逗号分隔，保持文件格式正确
            f.write("\n")  # 添加换行符分隔不同条数据
    if len(rlaif_data) > 0:
        with open(rlaif_path, "a", encoding='utf-8') as f:
            f.write(json.dumps(rlaif_data, ensure_ascii=False, indent=2)+",")  # 每条数据后添加逗号分隔，保持文件格式正确
            f.write("\n")  # 添加换行符分隔不同条数据


# 市场情绪分析数据构建器
async def sentiment_data_builder(stock_code: str, industry: str) -> tuple[dict, dict]:
    """构建市场情绪数据的输入输出格式"""
    try:
        sentiment_data: dict = json.loads(MarketSentimentTool(stock_code))
        stock_name = get_stock_base_data(stock_code)['name'].values[0]
        sentiment_info = sentiment_data.get("市场新闻", "N/A")[:5]  # 取前5条新闻作为情绪分析输入
        inputs = {"stock_code": stock_code, "stock_name": stock_name, "industry": industry, "sentiment_info": sentiment_info}

        raw_result = await SentimentAnalysisCrew().crew().akickoff(inputs=inputs)
        sentiment_results = json.loads(raw_result.raw)
        sft_data = sentiment_results["SFT"]
        rlaif_data = sentiment_results["RLAIF"]

        instruction = sft_data.get("instruction", "请根据提供的基本面数据进行分析，给出投资建议。")
        sft_data = {
            "instruction": instruction,
            "input": "",
            "output": sft_data.get("output", {})
        }

        return sft_data, rlaif_data
    except Exception as e:
        print(f"{stock_code}市场情绪分析数据构建失败: {e}")
        return {}, {}


# 市场情绪分析数据保存器
def sentiment_output_data_saver(sft_data: dict, rlaif_data: dict):
    """保存生成的市场情绪分析数据到本地文件"""
    sft_path = "dataset/senti/sentiment_analysis_SFT_test_data.json"
    rlaif_path = "dataset/senti/sentiment_analysis_RLAIF_test_data.json"

    if len(sft_data) > 0:
        with open(sft_path, "a", encoding='utf-8') as f:
            f.write(json.dumps(sft_data, ensure_ascii=False, indent=2)+",")  # 每条数据后添加逗号分隔，保持文件格式正确
            f.write("\n")  # 添加换行符分隔不同条数据

    if len(rlaif_data) > 0:
        with open(rlaif_path, "a", encoding='utf-8') as f:
            f.write(json.dumps(rlaif_data, ensure_ascii=False, indent=2)+",")  # 每条数据后添加逗号分隔，保持文件格式正确
            f.write("\n")  # 添加换行符分隔不同条数据


async def main():

    stock_arr = []

    for n, ind in enumerate(industry_info):
        industry_label = ind["industry_label"]
        industry = ind["industry"]

        industry_df = pd.DataFrame()
        try:
            industry_df = func_timeout(5, ak.stock_sector_detail, args=(industry_label,))
        except FunctionTimedOut:
            continue
        if industry_df.empty:
            print(f"行业 {industry_label} 未找到或无成分股")
        print(f"行业 {industry}")  # 输出行业成分股数量

        stock_codes = industry_df["symbol"].values.tolist()
        new_arr = random.sample(stock_codes, 1) # 每个行业随机选取1只股票进行构建，避免数据过多导致处理时间过长
        stock_arr.extend(new_arr)
        if n >= 20:  # 只处理前20个行业，避免数据过多导致处理时间过长
            break

    print(f"选取的股票列表: {stock_arr}")  # 输出选取的股票列表

    for stock_code in stock_arr:
        # 基本面分析数据构建
        print(f"处理基本面分析数据: {stock_code}")
        base_res = await base_data_builder(stock_code, industry)
        base_output_data_saver(base_res[0], base_res[1])

        # 技术面分析数据构建
        print(f"处理技术面分析数据: {stock_code}")
        technical_res = await technical_data_builder(stock_code, industry)
        technical_output_data_saver(technical_res[0], technical_res[1])

        # 市场情绪分析数据构建
        print(f"处理市场情绪分析数据: {stock_code}")
        sentiment_res = await sentiment_data_builder(stock_code, industry)
        sentiment_output_data_saver(sentiment_res[0], sentiment_res[1])


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())