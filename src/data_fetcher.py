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
    df = pd.read_csv(MASTER_FILE)
    return sorted(df['ticker'].unique().tolist())


def _eodhd_suffix(ticker: str) -> str:
    """Convert ticker to EODHD format (e.g., 000660.KS → 000660.KO)."""
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
            return past.iloc[-1]['close'] if not past.empty else None
        
        close_now = last['close']
        close_1d = prev['close']
        close_5d = get_past_close(7)   # ~1 week
        close_1m = get_past_close(30)  # ~1 month
        close_3m = get_past_close(90)  # ~3 months
        
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
            'volume': last['volume'],
        })
    
    return pd.DataFrame(results)


def run_fetch_pipeline():
    """Full pipeline: fetch prices → calculate returns → save."""
    # Fetch
    df_prices = fetch_prices(days_back=100)
    if df_prices.empty:
        print("[ERROR] No price data fetched!")
        return None
    
    # Save raw prices
    prices_file = PRICES_DIR / f"prices_{datetime.now().strftime('%Y%m%d')}.csv"
    df_prices.to_csv(prices_file, index=False)
    print(f"[SAVED] {prices_file} ({len(df_prices)} rows)")
    
    # Calculate returns
    df_returns = calculate_returns(df_prices)
    returns_file = BASE_DIR / "data" / "returns_latest.csv"
    df_returns.to_csv(returns_file, index=False)
    print(f"[SAVED] {returns_file} ({len(df_returns)} rows)")
    
    return df_returns


if __name__ == "__main__":
    run_fetch_pipeline()
