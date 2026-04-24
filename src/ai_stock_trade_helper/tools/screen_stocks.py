"""
股票筛选工具
按行业和基本面指标筛选 Top 股票
"""
import pandas as pd
import akshare as ak
import logging
from typing import List, Optional

from ai_stock_trade_helper.models import StockInfo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

exchange_map = {
                    'sh': '.SH',
                    'sz': '.SZ',
                    'bj': '.BJ',
                }

def screen_top_stocks_by_industry(
    industry_label: str,
    user_stock_codes: List[str] = [],
    top_n: int = 20,
    min_market_cap: float = 30,  # 最小流通市值（亿元）
    min_roe: float = 8,  # 最小净资产收益率 (%)
    min_net_margin: float = 3,  # 最小销售净利率 (%)
    max_debt_ratio: float = 70,  # 最大资产负债率 (%)
) -> List[StockInfo]:
    """
    按行业 + 通用基本面指标筛选 Top 股票
    
    Args:
        industry_name (str): 行业名称，例如：半导体、银行、医药生物、光伏设备、汽车整车
        top_n (int): 返回前N只股票，默认20
        min_market_cap (float): 最小流通市值（亿元），默认30
        min_trading_volume (float): 最小成交额（亿元），默认0.5
        min_roe (float): 最小净资产收益率 (%)，默认8
        min_net_margin (float): 最小销售净利率 (%)，默认3
        max_debt_ratio (float): 最大资产负债率 (%)，默认70
        
    Returns:
        Optional[pd.DataFrame]: 筛选结果DataFrame，包含关键财务指标；若筛选失败则返回None
    """
    try:
        logger.info(f"开始筛选行业: {industry_label}")
        
        # 1. 获取行业成分股
        industry_df = ak.stock_sector_detail(sector=industry_label)
        if industry_df.empty:
            logger.error(f"行业 {industry_label} 未找到或无成分股")
            return None
            
        stock_codes = industry_df["symbol"].values.tolist()
        logger.info(f"该行业共 {len(stock_codes)} 只股票，开始筛选...")
        
        # 2. 获取A 股基本面数据
        logger.info("获取基本面数据...")
        spot_data_list = []
        fin_data_list = []
        
        for code in stock_codes:
            try:
                # 获取财务基本面数据
                fin_data = get_stock_base_data(code)
            except Exception as e:
                logger.warning(f"获取股票 {code} 基本面数据失败: {e}")
                continue
            
            columns_to_select = [
                "name","扣非净利润", "销售净利率", "资产负债率", 
                "营业收入同比增长率", "归属净利润同比增长率", "净资产收益率", "经营现金流量"
            ]
            # 取最新日期的数据
            df = fin_data[columns_to_select].head(1)
            df["code"] = code  # 添加股票代码列
            # 填充空值
            df = df.fillna(0)
            # 基本过滤逻辑
            spot_df = df[
                # 盈利
                (df["净资产收益率"] >= min_roe) &
                (df["销售净利率"] >= min_net_margin) &
                (df["扣非净利润"] > 0) &
                # 现金流
                (df["经营现金流量"] > 0) &
                # 负债安全
                (df["资产负债率"] <= max_debt_ratio) &
                # 增长
                (df["营业收入同比增长率"] >= 0) &
                (df["归属净利润同比增长率"] >= 0) 
            ].copy()

            if spot_df.empty:
                logger.info(f"股票 {code} 不符合基本面筛选条件")
                continue
            
            # 获取流通市值数据
            try:
                symbol = str(code).upper()
                lt_data = ak.stock_zh_scale_comparison_em(symbol=symbol)
            except Exception as e:
                logger.warning(f"获取股票 {code} 流通市值失败: {e}")
                continue

            df = lt_data[["流通市值"]].head(1)
            df["code"] = code  # 添加股票代码列
            # 填充空值
            df = df.fillna(0)
            # 基本过滤逻辑
            fin_df = df[
                # 排雷
                (df["流通市值"] >= min_market_cap)
            ].copy()

            if fin_df.empty:
                logger.info(f"股票 {code} 不符合基本面筛选条件")
                continue

            spot_data_list.append(spot_df)
            fin_data_list.append(fin_df)

        spot_df = pd.concat(spot_data_list, ignore_index=True)
        fin_df = pd.concat(fin_data_list, ignore_index=True)

        finance_df = pd.merge(spot_df, fin_df, on="code", how="inner")
        
        logger.info(f"成功获取 {len(finance_df)} 条行情数据")
        
        # 确定使用哪个ROE列
        roe_col = "净资产收益率"
        margin_col = "销售净利率"
        
        df_sorted = finance_df.sort_values(
            by=[roe_col, margin_col],
            ascending=False
        ).head(top_n)
        
        logger.info(f"筛选完成，获得 {len(df_sorted)} 只符合条件的股票")
        
        results = df_sorted.reset_index(drop=True)

        logger.info(results.to_string(index=False))

        res_stocks = []

        for res in results.itertuples(index=False):
            res_stocks.append(StockInfo(stock_code=res.code, stock_name=res.name))

        if len(user_stock_codes) > 0:
            for code in user_stock_codes:
                if code in stock_codes:
                    fin_data = get_stock_base_data(code)
                    for res in fin_data.itertuples(index=False):
                        res_stocks.append(StockInfo(stock_code=res.code, stock_name=res.name))
        
        return res_stocks
    
    except Exception as e:
        logger.error(f"筛选过程中发生错误: {e}", exc_info=True)
        return None


def get_stock_base_data(code: str) -> pd.DataFrame:
    # 转换为小写以统一处理
    symbol_lower = str(code).lower()
    # 尝试匹配前缀（假设前缀长度为 2，但可调整）
    prefix_length = 2
    prefix = symbol_lower[:prefix_length]
    num_code = symbol_lower[prefix_length:]
    if prefix in exchange_map:
        symbol =  f"{num_code.upper()}{exchange_map[prefix]}"
    else:
        symbol = num_code.upper()  # 如果没有匹配到前缀，直接使用代码
    
    # 获取财务基本面数据
    fin_data = ak.stock_financial_analysis_indicator_em(
        symbol=symbol,
        indicator="按报告期"
    )
    # 重命名列名
    fin_data = fin_data.rename(columns={
        'SECURITY_NAME_ABBR': 'name',
        'KCFJCXSYJLR': '扣非净利润', 
        'XSJLL': '销售净利率', 
        'ZCFZL': '资产负债率', 
        'TOTALOPERATEREVETZ': '营业收入同比增长率', 
        'PARENTNETPROFITTZ': '归属净利润同比增长率',
        'ROEJQ': '净资产收益率',
        'JYXJLYYSR': '经营现金流量'
        })
    return fin_data

if __name__ == "__main__":
    # 示例：筛选半导体行业的优质股票
    result = screen_top_stocks_by_industry(
        industry_label="new_fdsb",
        top_n=20,
        min_market_cap=30,      # 流通市值 >= 30亿
        min_roe=8,              # ROE >= 8%
        min_net_margin=3,       # 销售净利率 >= 3%
        max_debt_ratio=70       # 资产负债率 <= 70%
    )
    
    if result is not None and not result.empty:
        print(f"\n找到 {len(result)} 只符合条件的股票:")
        print(result.to_string(index=False))
    else:
        print("未找到符合条件的股票")