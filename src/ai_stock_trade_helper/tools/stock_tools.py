"""股票数据获取工具"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import pandas as pd
import akshare as ak
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import logging
import json
import tushare as ts
from datetime import datetime, timedelta
from  dotenv import load_dotenv
import os

load_dotenv()

import requests
from ..util.caculate_func import (
    calculate_trend_signals,
    calculate_mean_reversion_signals,
    calculate_momentum_signals,
    calculate_volatility_signals,
    calculate_stat_arb_signals,
)

logger = logging.getLogger(__name__)


class StockCodeInput(BaseModel):
    """股票代码输入"""
    stock_code: str = Field(..., description="股票代码，如 sh600000 或 sz000001")


class GetStockBasicInfoTool(BaseTool):
    """获取股票基本信息工具"""
    name: str = "get_stock_basic_info"
    description: str = "获取指定股票的基本面指标信息，如ROE、净利率、市盈率等"
    args_schema: type[BaseModel] = StockCodeInput

    def _run(self, stock_code: str) -> str:
        indicator_list = [
                '净资产收益率(ROE)',
                '销售净利率',
                '毛利率',
                '总资产报酬率(ROA)',
                '营业总收入增长率',
                '基本每股收益',
                '流动比率', 
                '资产负债率',
                '每股现金流',
            ]
        try:
            stock_financial_abstract_df = ak.stock_financial_abstract(symbol=stock_code)
            latest_date_col = stock_financial_abstract_df.columns[2]
            df_new = stock_financial_abstract_df[['指标', latest_date_col]].copy().drop_duplicates()

            # 重置索引，让日期成为普通列（可选）
            df_new = df_new.set_index('指标').T.reset_index().rename(columns={'index': '日期'})
            df_new = df_new[indicator_list]
            df_new["代码"] = stock_code

            fin = ak.stock_zh_scale_comparison_em(symbol=stock_code.upper())
            fin['市盈率'] = fin['总市值']/ fin['净利润']
            fin['市销率'] = fin['总市值']/ fin['营业收入']
            fin_new = fin[['简称', '市盈率', '市销率']]
            fin_new["代码"] = stock_code

            res_df = df_new.merge(fin_new, on="代码", how="inner")

            json_data = res_df.to_dict(orient='records')[0]

            info = {
                "股票代码": json_data.get('代码', 'N/A'),
                "股票名称": json_data.get('简称', 'N/A'),
                "净资产收益率(ROE)": json_data.get('净资产收益率(ROE)', 'N/A'),
                "销售净利率": json_data.get('销售净利率', 'N/A'),
                "毛利率": json_data.get('毛利率', 'N/A'),
                "总资产报酬率(ROA)": json_data.get('总资产报酬率(ROA)', 'N/A'),
                "营业总收入增长率": json_data.get('营业总收入增长率', 'N/A'),
                "基本每股收益": json_data.get('基本每股收益', 'N/A'),
                "流动比率": json_data.get('流动比率', 'N/A'),
                "资产负债率": json_data.get('资产负债率', 'N/A'),
                "每股现金流": json_data.get('每股现金流', 'N/A'),
                "市盈率": json_data.get('市盈率', 'N/A'),
                "市销率": json_data.get('市销率', 'N/A')
            }
            return json.dumps(info, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            return f"获取股票 {stock_code} 基本信息失败: {str(e)}"


class GetStockTechnicalIndicatorsTool(BaseTool):
    """获取股票技术指标工具"""
    name: str = "get_stock_technical_indicators"
    description: str = "获取和计算股票的技术指标，如EMA、RSI、MACD等"
    args_schema: type[BaseModel] = StockCodeInput

    # Chinese mapping for indicators
    INDICATOR_MAPPING: dict = {
        "adx": "ADX指数",
        "trend_strength": "趋势强度",
        "ema_8": "8日EMA",
        "ema_21": "21日EMA",
        "ema_55": "55日EMA",
        "short_term_trend": "短期趋势",
        "medium_term_trend": "中期趋势",
        # Mean reversion signals
        "z_score": "Z评分",
        "price_vs_bb": "价格相对布林带位置",
        "rsi_14": "14日RSI",
        "rsi_28": "28日RSI",
        "bb_upper": "布林带上轨",
        "bb_lower": "布林带下轨",
        # Momentum signals
        "momentum_1m": "1月动量",
        "momentum_3m": "3月动量",
        "momentum_6m": "6月动量",
        "volume_momentum": "成交量动量",
        "momentum_score": "综合动量评分",
        "volume_confirmation": "成交量确认",
        # Volatility signals
        "historical_volatility": "历史波动率",
        "volatility_regime": "波动率体制",
        "volatility_z_score": "波动率Z评分",
        "atr_ratio": "ATR比率",
        # Stat arb signals
        "hurst_exponent": "赫斯特指数",
        "skewness": "偏度",
        "kurtosis": "峰度",
    }

    def _run(self, stock_code: str) -> str:
        try:
            price_data: pd.DataFrame = self.getStockPrice(stock_code)

            if price_data.empty:
                return json.dumps({"error": f"无法获取 {stock_code} 的价格数据"}, ensure_ascii=False, indent=2)

            # Calculate technical indicators
            tech_indicators = {
                "股票代码": stock_code,
            }

            # Calculate trend signals
            trend_signals = calculate_trend_signals(price_data)
            tech_indicators["趋势分析"] = self._translate_metrics(trend_signals["metrics"])

            # Calculate mean reversion signals
            mean_reversion_signals = calculate_mean_reversion_signals(price_data)
            tech_indicators["均值回归分析"] = self._translate_metrics(mean_reversion_signals["metrics"])

            # Calculate momentum signals
            momentum_signals = calculate_momentum_signals(price_data)
            tech_indicators["动量分析"] = self._translate_metrics(momentum_signals["metrics"])

            # Calculate volatility signals
            volatility_signals = calculate_volatility_signals(price_data)
            tech_indicators["波动率分析"] = self._translate_metrics(volatility_signals["metrics"])

            # Calculate statistical arbitrage signals
            stat_arb_signals = calculate_stat_arb_signals(price_data)
            tech_indicators["统计套利分析"] = self._translate_metrics(stat_arb_signals["metrics"])

            return json.dumps(tech_indicators, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"获取技术指标失败: {e}")
            return json.dumps({"error": f"获取股票 {stock_code} 技术指标失败: {str(e)}"}, ensure_ascii=False, indent=2)
        
    def getStockPrice(stock_code: str) -> pd.DataFrame:
        try:
            tuShareToken = os.getenv("TUSHARE_TOKEN")
            ts.set_token(tuShareToken)
            pro = ts.pro_api()

            # 计算日期：今天 ~ 6 个月前
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
            
            # 获取日 K 线数据
            df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)

            # 重命名列，更直观
            df.rename(columns={
                "trade_date": "Date",
                "vol": "volume",
            }, inplace=True)

            # 只保留你要的字段
            result = df[["Date", "open", "high", "low", "close", "volume"]]
            return result

        except Exception as e:
            logger.error(f"获取股票价格数据异常: {e}")
            return pd.DataFrame()

    def _translate_metrics(self, metrics_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Translate metrics dictionary to Chinese with rounded values"""
        translated = {}

        for key, value in metrics_dict.items():
            chinese_key = self.INDICATOR_MAPPING.get(key, key)
            # Round numeric values to 4 decimal places
            if isinstance(value, (int, float)):
                translated[chinese_key] = round(float(value), 4)
            else:
                translated[chinese_key] = value

        return translated


class GetMarketSentimentTool(BaseTool):
    """获取市场情绪工具"""
    name: str = "get_market_sentiment"
    description: str = "获取股票的市场情绪数据，包括新闻热度、舆情评分等"
    args_schema: type[BaseModel] = StockCodeInput

    def _run(self, stock_code: str) -> str:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://vip.stock.finance.sina.com.cn/"
            }
            news_list = []
            pages = 1  # 抓取前1页新闻

            for page in range(1, pages+1):
                url = f"https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php?symbol={stock_code}&Page={page}"
                resp = requests.get(url, headers=headers)
                # resp.encoding = "utf-8"
                soup = BeautifulSoup(resp.text, "html.parser")

                datelist_div = soup.find("div", class_="datelist")
                if datelist_div:
                    # 将 <br> 替换为换行符，方便按行分割
                    for br in datelist_div.find_all("br"):
                        br.replace_with("\n")

                    text = datelist_div.get_text()
                    lines = [line.strip() for line in text.split("\n") if line.strip()]

                    # 清理多余的 &nbsp; 和空格
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 3:
                            date = parts[0]
                            time = parts[1]
                            title = " ".join(parts[2:])
                            news_list.append({"datetime": f"{date} {time}", "title": title})
            res_data = news_list

            sentiment_info = {
                "股票代码": stock_code,
                "市场新闻": res_data
            }

            return json.dumps(sentiment_info, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"获取市场情绪失败: {e}")
            return f"获取股票 {stock_code} 市场情绪失败: {str(e)}"
