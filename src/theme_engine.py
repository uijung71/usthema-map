"""
theme_engine.py — Theme-level analytics engine
Aggregates stock returns into theme/category performance.
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_FILE = BASE_DIR / "data" / "theme_master.csv"
RETURNS_FILE = BASE_DIR / "data" / "returns_latest.csv"

# Category display config
CATEGORY_CONFIG = {
    '기술 패권 & 디지털 혁신': {'icon': '🔧', 'color': '#00d4ff'},
    '에너지 주권 & 지구의 미래': {'icon': '⚡', 'color': '#00e676'},
    '바이오 혁명 & 인류의 진화': {'icon': '🧬', 'color': '#e040fb'},
    '신공급망 & 국가 안보': {'icon': '🛡️', 'color': '#ff9100'},
    '미래 소비 & 라이프스타일': {'icon': '🛍️', 'color': '#ffea00'},
}


def load_master():
    """Load theme master mapping."""
    return pd.read_csv(MASTER_FILE)


def load_returns():
    """Load latest returns data."""
    if RETURNS_FILE.exists():
        return pd.read_csv(RETURNS_FILE)
    return pd.DataFrame()


def get_theme_returns(return_col='return_1d'):
    """
    Calculate theme-level returns by averaging stock returns.
    Returns DataFrame: [theme_id, theme_name, category, avg_return, top_stock, ...]
    """
    master = load_master()
    returns = load_returns()
    
    if returns.empty:
        return pd.DataFrame()
    
    # Merge returns into master
    merged = master.merge(returns, on='ticker', how='left')
    
    # Theme-level aggregation (stocks only, not ETFs)
    stocks = merged[merged['type'] == 'stock']
    
    theme_agg = stocks.groupby(['theme_id', 'theme_name', 'category']).agg(
        avg_return=(return_col, 'mean'),
        max_return=(return_col, 'max'),
        min_return=(return_col, 'min'),
        stock_count=('ticker', 'count'),
    ).reset_index()
    
    # Add top performer per theme
    top_stocks = stocks.loc[stocks.groupby('theme_id')[return_col].idxmax()]
    top_map = top_stocks.set_index('theme_id')[['ticker', return_col]].rename(
        columns={'ticker': 'top_ticker', return_col: 'top_return'}
    )
    theme_agg = theme_agg.merge(top_map, on='theme_id', how='left')
    
    return theme_agg.sort_values('avg_return', ascending=False)


def get_category_returns(return_col='return_1d'):
    """Calculate category-level (대분류) average returns."""
    theme_df = get_theme_returns(return_col)
    if theme_df.empty:
        return pd.DataFrame()
    
    cat_agg = theme_df.groupby('category').agg(
        avg_return=('avg_return', 'mean'),
        best_theme=('theme_name', lambda x: x.iloc[0]),  # already sorted
        theme_count=('theme_id', 'count'),
    ).reset_index()
    
    return cat_agg.sort_values('avg_return', ascending=False)


def get_theme_detail(theme_id: int):
    """Get detailed info for a specific theme including all stocks and ETFs."""
    master = load_master()
    returns = load_returns()
    
    theme_rows = master[master['theme_id'] == theme_id]
    if theme_rows.empty:
        return None, pd.DataFrame(), pd.DataFrame()
    
    meta = {
        'theme_id': theme_id,
        'theme_name': theme_rows.iloc[0]['theme_name'],
        'category': theme_rows.iloc[0]['category'],
    }
    
    # Stocks
    stocks = theme_rows[theme_rows['type'] == 'stock']
    if not returns.empty:
        stocks = stocks.merge(returns, on='ticker', how='left')
    
    # ETFs
    etfs = theme_rows[theme_rows['type'] == 'etf']
    if not returns.empty:
        etfs = etfs.merge(returns, on='ticker', how='left')
    
    return meta, stocks, etfs


def get_theme_list():
    """Get simple theme list for dropdowns."""
    master = load_master()
    return master[['theme_id', 'theme_name', 'category']].drop_duplicates().sort_values('theme_id')
