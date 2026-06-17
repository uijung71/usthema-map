"""
data_fetcher.py — EODHD API price fetcher for 420 theme stocks/ETFs
Fetches end-of-day prices, calculates daily/weekly/monthly returns.
"""

import os
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("EODHD_API_KEY", "")
BASE_DIR = Path(__file__).resolve().parent.parent
PRICES_DIR = BASE_DIR / "data" / "prices"
MASTER_FILE = BASE_DIR / "data" / "theme_master.csv"


def get_all_tickers():
    """Get unique tickers from theme_master.csv."""
    df = pd.read_csv(MASTER_FILE, encoding='utf-8-sig')
    return sorted(df['ticker'].unique().tolist())


def _eodhd_suffix(ticker: str) -> str:
    """Convert ticker to EODHD format (e.g., 000660.KS → 000660.KO)."""
    # Manual overrides for typos or specific exchanges
    overrides = {
        'SK하이닉스': '000660.KO',
        'TSMC': 'TSM.US',
        '삼성바이오로직스': '207940.KO',
    }
    if ticker in overrides:
        return overrides[ticker]
        
    if ticker.endswith('.KS'):
        return ticker.replace('.KS', '.KO')  # EODHD uses .KO for Korea
    if ticker.endswith('.HK'):
        return ticker  # Hong Kong tickers are the same
    return f"{ticker}.US"


def fetch_prices(tickers: list = None, days_back: int = 90) -> pd.DataFrame:
    """
    Fetch EOD prices from EODHD for all theme tickers.
    Returns DataFrame with columns: [date, ticker, close, volume]
    """
    if tickers is None:
        tickers = get_all_tickers()
    
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    all_data = []
    success, fail = 0, 0
    
    print(f"[EODHD] Fetching {len(tickers)} tickers from {from_date}...", flush=True)
    
    for ticker in tickers:
        eodhd_sym = _eodhd_suffix(ticker)
        
        # Use yfinance for Korean stocks since EODHD returns dummy data (999999.99)
        if eodhd_sym.endswith('.KO'):
            yf_sym = eodhd_sym.replace('.KO', '.KS')
            import yfinance as yf
            try:
                hist = yf.Ticker(yf_sym).history(start=from_date)
                for date, row in hist.iterrows():
                    all_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'ticker': ticker,
                        'close': float(row['Close']),
                        'volume': int(row['Volume']),
                    })
                success += 1
            except Exception as e:
                print(f"[YF] Failed for {ticker}: {e}")
                fail += 1
            continue

        url = f"https://eodhd.com/api/eod/{eodhd_sym}"
        params = {
            "api_token": API_KEY,
            "fmt": "json",
            "period": "d",
            "from": from_date,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    for row in data:
                        all_data.append({
                            'date': row['date'],
                            'ticker': ticker,
                            'close': float(row.get('adjusted_close', row.get('close', 0))),
                            'volume': int(row.get('volume', 0)),
                        })
                    success += 1
                else:
                    fail += 1
            else:
                fail += 1
        except Exception:
            fail += 1
        
        time.sleep(0.08)  # Rate limiting (12 req/sec)
    
    print(f"[EODHD] Done: {success} success, {fail} failed", flush=True)
    
    if not all_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['ticker', 'date']).reset_index(drop=True)
    return df


def calculate_returns(df_prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily, weekly (5d), monthly (21d) returns per ticker."""
    results = []
    latest_date = df_prices['date'].max()
    
    for ticker, grp in df_prices.groupby('ticker'):
        grp = grp.sort_values('date')
        if len(grp) < 2:
            continue
        
        last = grp.iloc[-1]
        prev = grp.iloc[-2] if len(grp) >= 2 else last
        
        # Find price N days back
        def get_past_close(n_days):
            target = latest_date - timedelta(days=n_days)
            past = grp[grp['date'] <= target]
            if not past.empty:
                return past.iloc[-1]['close']
            else:
                # Fallback to the first available price (IPO price)
                return grp.iloc[0]['close']
        
        close_now = last['close']
        close_1d = prev['close']
        close_5d = get_past_close(7)   # ~1 week
        close_1m = get_past_close(30)  # ~1 month
        close_3m = get_past_close(90)  # ~3 months
        close_6m = get_past_close(180) # ~6 months
        close_1y = get_past_close(365) # ~1 year
        
        def pct(curr, prev_val):
            if prev_val and prev_val > 0:
                return (curr - prev_val) / prev_val * 100
            return 0
        
        results.append({
            'ticker': ticker,
            'close': close_now,
            'date': last['date'],
            'return_1d': pct(close_now, close_1d),
            'return_1w': pct(close_now, close_5d),
            'return_1m': pct(close_now, close_1m),
            'return_3m': pct(close_now, close_3m),
            'return_6m': pct(close_now, close_6m),
            'return_1y': pct(close_now, close_1y),
            'volume': last['volume'],
        })
    
    return pd.DataFrame(results)


def fetch_market_caps(tickers: list = None) -> pd.DataFrame:
    """Fetch market caps for all tickers using yfinance fast_info."""
    if tickers is None:
        tickers = get_all_tickers()
    
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor
    
    print(f"[YF] Fetching market caps for {len(tickers)} tickers...", flush=True)
    results = []
    
    def get_cap(t):
        try:
            # Map ticker to yfinance format
            eodhd_sym = _eodhd_suffix(t)
            yf_sym = eodhd_sym.replace('.US', '')
            if yf_sym.endswith('.KO'):
                yf_sym = yf_sym.replace('.KO', '.KS')
                
            # fast_info is much faster than .info
            cap = yf.Ticker(yf_sym).fast_info.market_cap
            if cap:
                # Convert to Billions
                return {'ticker': t, 'mcap': cap / 1e9}
        except Exception:
            pass
        return {'ticker': t, 'mcap': 1.0} # Fallback 1B if failed
        
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(get_cap, tickers))
        
    df_mcap = pd.DataFrame(results)
    return df_mcap


def run_fetch_pipeline():
    """Full pipeline: fetch prices → calculate returns → fetch mcaps → save."""
    # Fetch 380 days back to cover 1 year (365 days) plus buffer
    df_prices = fetch_prices(days_back=380)
    if df_prices.empty:
        print("[ERROR] No price data fetched!")
        return None
    
    # Save raw prices
    prices_file = PRICES_DIR / f"prices_{datetime.now().strftime('%Y%m%d')}.csv"
    df_prices.to_csv(prices_file, index=False, encoding='utf-8-sig')
    print(f"[SAVED] {prices_file} ({len(df_prices)} rows)")
    
    # Calculate returns
    df_returns = calculate_returns(df_prices)
    returns_file = BASE_DIR / "data" / "returns_latest.csv"
    df_returns.to_csv(returns_file, index=False, encoding='utf-8-sig')
    print(f"[SAVED] {returns_file} ({len(df_returns)} rows)")
    
    # Fetch and save market caps
    df_mcap = fetch_market_caps(get_all_tickers())
    mcap_file = BASE_DIR / "data" / "mcap_latest.csv"
    df_mcap.to_csv(mcap_file, index=False, encoding='utf-8-sig')
    print(f"[SAVED] {mcap_file} ({len(df_mcap)} rows)")
    
    return df_returns


def get_etf_fundamentals_yf(ticker: str) -> dict:
    """
    Fallback: Fetch ETF data from Yahoo Finance using yfinance.
    """
    import yfinance as yf
    try:
        etf = yf.Ticker(ticker)
        info = etf.info
        
        # Try even more fee keys
        fee = info.get('feesEntity_annualReportExpenseRatio')
        for k in ['annualReportExpenseRatio', 'expenseRatio', 'netExpenseRatio', 'annualHoldingsCost', 'totalExpenseRatio']:
            if fee is None: fee = info.get(k)
        
        # AUM keys (be aggressive)
        aum = info.get('totalAssets')
        if aum is None: aum = info.get('marketCap')
        if aum is None: aum = info.get('navPrice')
        
        # Name cleanup
        long_name = info.get('longName', ticker)
        if long_name:
            long_name = long_name.replace('Invesco ', '').replace('iShares ', '').replace('Global X ', '').replace('SPDR ', '')
        
        # Format to match a similar structure for easy processing
        data = {
            'General': {
                'Name': long_name,
                'Description': info.get('longBusinessSummary', ''),
                'UpdatedAt': datetime.now().strftime('%Y-%m-%d')
            },
            'ETF_Data': {
                'Expense_Ratio': fee if fee is not None else 0,
                'Asset_Under_Management': aum if aum is not None else 0,
                'Holdings': []
            }
        }
        
        # Try to get holdings
        holdings = None
        if hasattr(etf, 'funds_data') and etf.funds_data.top_holdings is not None:
            holdings = etf.funds_data.top_holdings
            
        if holdings is not None:
            for symbol, row in holdings.iterrows():
                data['ETF_Data']['Holdings'].append({
                    'Code': symbol,
                    'Name': row.get('Name', ''),
                    'Assets_%': row.get('Holding Percent', 0) * 100
                })
        return data
    except Exception as e:
        print(f"[YF ERROR] Failed for {ticker}: {e}")
    return {}


def get_etf_fundamentals(ticker: str) -> dict:
    """
    Fetch ETF fundamental data. 
    Tries Local Cache -> yfinance (Preferred for now due to EODHD 403) -> EODHD.
    """
    cache_dir = BASE_DIR / "data" / "cache" / "etf_fundamentals"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{ticker}.json"
    
    # 1. Check Cache (valid for 3 days)
    if cache_file.exists():
        age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if age.days < 3:
            try:
                import json
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

    # 2. Try yfinance first (since EODHD 403 was confirmed for this key)
    print(f"[FETCH] Trying yfinance for {ticker}...")
    data = get_etf_fundamentals_yf(ticker)
    
    # 3. Fallback to EODHD (if yfinance failed and we want to try)
    if not data:
        print(f"[FETCH] Falling back to EODHD for {ticker}...")
        eodhd_sym = _eodhd_suffix(ticker)
        url = f"https://eodhd.com/api/fundamentals/{eodhd_sym}"
        params = {"api_token": API_KEY, "fmt": "json"}
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
        except Exception:
            pass

    # 4. Save to Cache if success and data is valid
    if data and 'ETF_Data' in data:
        try:
            import json
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
            
    return data


if __name__ == "__main__":
    run_fetch_pipeline()
