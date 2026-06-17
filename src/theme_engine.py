"""
theme_engine.py — Theme-level analytics engine
Aggregates stock returns into theme/category performance.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_FILE = BASE_DIR / "data" / "theme_master.csv"
RETURNS_FILE = BASE_DIR / "data" / "returns_latest.csv"
PRICES_DIR = BASE_DIR / "data" / "prices"

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
    df = pd.read_csv(MASTER_FILE, encoding='utf-8-sig')
    if 'category' in df.columns:
        # Strip trailing parenthesized English, e.g. " (Geopolitics & Infrastructure)" -> "신공급망 & 국가 안보"
        df['category'] = df['category'].str.replace(r'\s*\([^)]*\)', '', regex=True).str.strip()
    return df


def load_returns():
    """Load latest returns data."""
    if RETURNS_FILE.exists():
        return pd.read_csv(RETURNS_FILE)
    return pd.DataFrame()


@st.cache_data(ttl=60)
def _load_mcap_dict():
    try:
        mcap_file = BASE_DIR / "data" / "mcap_latest.csv"
        df = pd.read_csv(mcap_file)
        return dict(zip(df['ticker'], df['mcap']))
    except Exception as e:
        print(f"Error loading mcap data: {e}")
        return {}


def get_market_cap(ticker):
    """Estimate market cap for weighting. Reads from mcap_latest.csv."""
    mcap_dict = _load_mcap_dict()
    val = mcap_dict.get(ticker)
    if val and val > 0:
        return val
    return 1.0  # Fallback


def get_theme_returns(return_col='return_1d'):
    """
    Calculate theme-level returns and weights.
    Returns DataFrame: [theme_id, theme_name, category, avg_return, theme_weight, ...]
    """
    master = load_master()
    returns = load_returns()
    
    if returns.empty:
        return pd.DataFrame()
    
    # Merge returns into master
    merged = master.merge(returns, on='ticker', how='left')
    
    # Add individual market cap for weighting
    merged['mcap'] = merged['ticker'].apply(get_market_cap)
    
    # Theme-level aggregation (stocks only, not ETFs)
    stocks = merged[merged['type'] == 'stock']
    
    theme_agg = stocks.groupby(['theme_id', 'theme_name', 'category']).agg(
        avg_return=(return_col, 'mean'),
        max_return=(return_col, 'max'),
        min_return=(return_col, 'min'),
        stock_count=('ticker', 'count'),
        theme_weight=('mcap', 'sum'),
    ).reset_index()
    
    # Add top performer per theme
    stocks_valid = stocks.copy()
    stocks_valid[return_col] = stocks_valid[return_col].fillna(-999)
    
    top_stocks = stocks_valid.loc[stocks_valid.groupby('theme_id')[return_col].idxmax()]
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


def get_stock_level_data(return_col='return_1d'):
    """
    Get granular stock-level data merged with theme info.
    Used for 3-level treemap (Category > Theme > Stock).
    """
    master = load_master()
    returns = load_returns()
    
    if returns.empty:
        return pd.DataFrame()
    
    # Merge returns into master
    merged = master.merge(returns, on='ticker', how='left')
    
    # Add individual market cap
    merged['mcap'] = merged['ticker'].apply(get_market_cap)
    
    # Filter for stocks only for the treemap (ETFs can be shown separately)
    stocks = merged[merged['type'] == 'stock'].copy()
    
    # Fill NaN returns
    stocks[return_col] = stocks[return_col].fillna(0)
    
    return stocks


def get_etf_level_data(return_col='return_1d'):
    """
    Get granular ETF-level data merged with theme info.
    Used for the ETF Theme Board.
    """
    master = load_master()
    returns = load_returns()
    
    if returns.empty:
        return pd.DataFrame()
    
    # Merge returns into master
    merged = master.merge(returns, on='ticker', how='left')
    
    # Filter for ETFs only
    etfs = merged[merged['type'] == 'etf'].copy()
    
    # Fill NaN returns
    etfs[return_col] = etfs[return_col].fillna(0)
    
    return etfs


def get_theme_list():
    """Get simple theme list for dropdowns."""
    master = load_master()
    return master[['theme_id', 'theme_name', 'category']].drop_duplicates().sort_values('theme_id')


def get_theme_historical_trend(theme_names, period_key):
    """
    Calculates daily cumulative returns for selected themes over the chosen period.
    period_key: 'return_1d', 'return_1w', 'return_1m', 'return_3m', 'return_6m', 'return_1y'
    """
    # 1. Find latest price file
    price_files = sorted(list(PRICES_DIR.glob("prices_*.csv")))
    if not price_files:
        return pd.DataFrame()
    latest_price_file = price_files[-1]
    
    try:
        df_prices = pd.read_csv(latest_price_file)
        df_prices['date'] = pd.to_datetime(df_prices['date'])
    except Exception:
        return pd.DataFrame()
        
    # 2. Filter by period
    latest_date = df_prices['date'].max()
    period_days = {
        'return_1d': 7,    # 1D selection -> show 7 days trend
        'return_1w': 14,   # 1W selection -> show 14 days trend
        'return_1m': 35,
        'return_3m': 100,
        'return_6m': 200,
        'return_1y': 400
    }
    days = period_days.get(period_key, 35)
    start_date = latest_date - timedelta(days=days)
    df_prices = df_prices[df_prices['date'] >= start_date].copy()
    
    # 3. Join with master
    master = load_master()
    merged = df_prices.merge(master[['ticker', 'theme_name', 'type']], on='ticker')
    stocks = merged[merged['type'] == 'stock']
    stocks = stocks[stocks['theme_name'].isin(theme_names)]
    
    if stocks.empty:
        return pd.DataFrame()
        
    # 4. Calculate daily returns per ticker
    stocks = stocks.sort_values(['ticker', 'date'])
    stocks['daily_ret'] = stocks.groupby('ticker')['close'].pct_change()
    
    # 5. Average daily returns by theme per date
    theme_daily = stocks.dropna(subset=['daily_ret']).groupby(['theme_name', 'date'])['daily_ret'].mean().reset_index()
    
    # 6. Cumulative returns
    theme_daily = theme_daily.sort_values(['theme_name', 'date'])
    
    # Calculate cumulative growth: (1 + r1)*(1 + r2)... - 1
    theme_daily['value'] = theme_daily.groupby('theme_name')['daily_ret'].transform(lambda x: (1 + x).cumprod() - 1)
    theme_daily['value'] = theme_daily['value'] * 100 # %
    
    return theme_daily

def get_etf_historical_trend(tickers, period_key):
    """
    Calculates daily cumulative returns for selected ETFs over the chosen period.
    period_key: 'return_1d', 'return_1w', 'return_1m', 'return_3m', 'return_6m', 'return_1y'
    """
    # 1. Find latest price file
    price_files = sorted(list(PRICES_DIR.glob("prices_*.csv")))
    if not price_files:
        return pd.DataFrame()
    latest_price_file = price_files[-1]
    
    try:
        df_prices = pd.read_csv(latest_price_file)
        df_prices['date'] = pd.to_datetime(df_prices['date'])
    except Exception:
        return pd.DataFrame()
        
    # 2. Filter by period
    latest_date = df_prices['date'].max()
    period_days = {
        'return_1d': 7,
        'return_1w': 14,
        'return_1m': 35,
        'return_3m': 100,
        'return_6m': 200,
        'return_1y': 400
    }
    days = period_days.get(period_key, 35)
    start_date = latest_date - timedelta(days=days)
    df_prices = df_prices[df_prices['date'] >= start_date].copy()
    
    # 3. Filter by tickers
    df_prices = df_prices[df_prices['ticker'].isin(tickers)]
    if df_prices.empty:
        return pd.DataFrame()
        
    # 4. Calculate daily returns per ticker
    df_prices = df_prices.sort_values(['ticker', 'date'])
    df_prices['daily_ret'] = df_prices.groupby('ticker')['close'].pct_change()
    
    # 5. Cumulative returns
    df_prices = df_prices.dropna(subset=['daily_ret'])
    df_prices['value'] = df_prices.groupby('ticker')['daily_ret'].transform(lambda x: (1 + x).cumprod() - 1)
    df_prices['value'] = df_prices['value'] * 100 # %
    
    return df_prices[['date', 'ticker', 'value']]
    
# ── ETF Korean Knowledge Base ────────────────────────────────────
ETF_KOREAN_INFO = {
    # 반도체 / AI
    'SOXX': {'name': '반도체 지수 ETF', 'desc': '미국 상장 반도체 기업 30종목에 투자하는 대표적인 반도체 지수 상품입니다. 엔비디아, 브로드컴 등 핵심 칩 제조사에 집중 투자합니다.'},
    'SOXQ': {'name': '반도체 설계/제조 ETF', 'desc': '반도체 설계 및 제조 전반에 걸쳐 포트폴리오를 구성하며, 저렴한 수수료로 장기 투자에 유리한 반도체 테마 ETF입니다.'},
    'SMH': {'name': '반도체 핵심주 ETF', 'desc': '글로벌 반도체 산업의 거인들을 가장 공격적으로 담고 있는 ETF로, 상위 종목 비중이 높아 변동성이 크지만 수익률이 강력합니다.'},
    'AIQ': {'name': 'AI & 빅데이터 ETF', 'desc': '인공지능 기술 개발과 이를 활용하는 하드웨어, 소프트웨어 기업들에 광범위하게 투자하는 AI 테마 전문 상품입니다.'},
    'BOTZ': {'name': '로봇 및 인공지능 ETF', 'desc': '산업용 로봇부터 자율주행, AI 알고리즘까지 미래 산업의 핵심인 자동화 기술 관련 글로벌 리더들에 투자합니다.'},
    'ROBO': {'name': '로보틱스 전문 ETF', 'desc': '전 세계 로봇 및 자동화 기기 제조사들에 고르게 분산 투자하여 안정적인 성장을 추구하는 테마형 ETF입니다.'},
    'CHAT': {'name': '생성형 AI 전문 ETF', 'desc': 'ChatGPT 등 생성형 AI 기술과 관련된 클라우드, 데이터 센터, 소프트웨어 플랫폼 기업들을 집중적으로 담고 있습니다.'},
    
    # 에너지 / 탄소 / 인프라
    'ICLN': {'name': '친환경 에너지 ETF', 'desc': '태양광, 풍력 등 전 세계 신재생 에너지 관련 기업 100여 개에 투자하는 전 세계에서 가장 큰 친환경 테마 ETF입니다.'},
    'TAN': {'name': '태양광 산업 ETF', 'desc': '태양광 패널 제조 및 에너지 솔루션 기업들에 집중 투자하며, 탄소 중립 정책의 수혜를 가장 직접적으로 입는 테마입니다.'},
    'URA': {'name': '우라늄 및 원자력 ETF', 'desc': '원자력 발전의 원료인 우라늄 채굴 기업과 원자로 설계사 등 원자력 에너지 밸류체인 전반에 투자합니다.'},
    'LIT': {'name': '리튬 & 2차전지 ETF', 'desc': '전기차 배터리의 핵심인 리튬 채굴부터 배터리 셀 제조사까지, 에너지 저장 장치 산업의 글로벌 리더들을 포함합니다.'},
    'PAVE': {'name': '미국 인프라 재건 ETF', 'desc': '미국 정부의 인프라 투자 정책으로 수혜를 입는 건설, 원자재, 장비 관련 기업들에 집중 투자하는 인프라 테마입니다.'},
    
    # 우주 / 국방
    'DFEN': {'name': '우주항공 & 국방 레버리지', 'desc': '미국 국방 예산 집행의 수혜를 입는 방산 업체와 우주 항공 기업 지수를 3배로 추종하여 강력한 수익률을 추구합니다.'},
    'UFO': {'name': '우주 산업 전문 ETF', 'desc': '위성 통신, 우주 탐사 서비스 등 미래 우주 경제를 이끌어갈 혁신 기업들에 투자하는 독보적인 우주 테마 상품입니다.'},
    'PPA': {'name': '미국 국방 & 우주 ETF', 'desc': '안정적인 수익성을 자랑하는 미국 핵심 방위 산업체들에 분산 투자하여 안보 위기 상황에서 강력한 방어력을 보여줍니다.'},
    
    # 바이오 / 헬스케어
    'XBI': {'name': '미국 바이오텍 ETF', 'desc': '신약 개발 및 유전자 편집 기술을 보유한 미국 중소형 바이오 기업들에 동일 비중으로 투자하여 폭발적인 성장을 기대하는 상품입니다.'},
    'XLV': {'name': '헬스케어 섹터 ETF', 'desc': '대형 제약사, 의료 기기, 건강 보험 등 미국 헬스케어 산업의 우량 종목들을 모두 담고 있는 가장 안정적인 헬스케어 ETF입니다.'},
    'ARKG': {'name': '유전공학 혁신 ETF', 'desc': '게놈 편집, 분자 진단 등 인류의 진화를 이끌 바이오 혁신 기업들에 적극적으로 투자하는 액티브 테마 상품입니다.'},
    
    # 기타 테마
    'QQQ': {'name': '나스닥 100 지수 ETF', 'desc': '미국 나스닥 시장의 핵심 기술주 100종목을 추종하며, 전 세계에서 가장 거래량이 많고 검증된 성장주 ETF입니다.'},
    'VNQ': {'name': '미국 리츠(부동산) ETF', 'desc': '미국 상업용 부동산, 주거용 리츠 등에 광범위하게 투자하여 안정적인 배당 수익과 자산 가치 상승을 동시에 추구합니다.'},
    'MSOS': {'name': '미국 대마초 테마 ETF', 'desc': '미국 연방 정부의 규제 완화 수혜를 기대하며 의료용 및 기호용 대마 산업 리더들에 투자하는 고위험 고수익 상품입니다.'},
    'BETZ': {'name': '스포츠 배팅 & 카지노 ETF', 'desc': '온라인 스포츠 배팅 시장의 성장과 함께 카지노, 온라인 게임 플랫폼 등 엔터테인먼트 산업에 투자하는 테마입니다.'},
    'METV': {'name': '메타버스 전문 ETF', 'desc': '가상 세계 구현을 위한 그래픽 카드, 엔진 개발, 플랫폼 운영 기업 등 메타버스 생태계 전반을 아우르는 투자 상품입니다.'},
}

def get_etf_details(ticker: str) -> dict:
    """
    Get structured ETF details (AUM, Fees, Holdings) for the UI with professional Korean support.
    """
    from src.data_fetcher import get_etf_fundamentals
    raw = get_etf_fundamentals(ticker)
    
    # Basic fallbacks if no raw data (API 403 etc)
    general = raw.get('General', {})
    etf_data = raw.get('ETF_Data', {})
    
    # Use mapping for Korean name/desc if available
    k_info = ETF_KOREAN_INFO.get(ticker, {})
    full_name = k_info.get('name', general.get('Name', ticker))
    
    # Force Korean Description (No English allowed)
    description = k_info.get('desc')
    if not description:
        # Generate a descriptive Korean sentence based on common patterns if missing
        description = f"본 상품은 {ticker} 지수를 기반으로 해당 테마의 글로벌 핵심 우량 기업들에 투자하는 전문 ETF입니다. "
        description += "장기적 성장 잠재력이 높은 산업 분야를 엄선하여 포트폴리오를 구성하고 있습니다."
            
    details = {
        'ticker': ticker,
        'full_name': full_name,
        'description': description,
        'updated_at': general.get('UpdatedAt', ''),
        'expense_ratio': etf_data.get('Expense_Ratio', 0),
        'aum': etf_data.get('Asset_Under_Management', 0),
        'holdings': []
    }
    
    # Process Holdings
    raw_holdings = etf_data.get('Holdings', {})
    if raw_holdings:
        if isinstance(raw_holdings, dict):
            h_list = list(raw_holdings.values())
        else:
            h_list = raw_holdings
            
        for h in h_list:
            details['holdings'].append({
                'ticker': h.get('Code', ''),
                'name': h.get('Name', ''),
                'weight': h.get('Assets_%', 0)
            })
        details['holdings'] = sorted(details['holdings'], key=lambda x: x['weight'], reverse=True)
        
    return details
