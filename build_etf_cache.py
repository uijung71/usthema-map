"""
build_etf_cache.py - Pre-fetch all ETF fundamentals and save to cache
Run this script to populate data/cache/etf_fundamentals/ before deployment.
"""

import sys
import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
MASTER_FILE = BASE_DIR / "data" / "theme_master.csv"
CACHE_DIR = BASE_DIR / "data" / "cache" / "etf_fundamentals"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_etf_fundamentals_yf(ticker: str) -> dict:
    import yfinance as yf
    try:
        etf = yf.Ticker(ticker)
        info = etf.info

        # Expense ratio
        fee = None
        for k in ['feesEntity_annualReportExpenseRatio', 'annualReportExpenseRatio',
                  'expenseRatio', 'netExpenseRatio', 'annualHoldingsCost', 'totalExpenseRatio']:
            if fee is None:
                fee = info.get(k)

        # AUM
        aum = info.get('totalAssets') or info.get('marketCap') or 0

        # Name
        long_name = info.get('longName', ticker)
        for prefix in ['Invesco ', 'iShares ', 'Global X ', 'SPDR ', 'VanEck ', 'ARK ']:
            if long_name:
                long_name = long_name.replace(prefix, '')

        data = {
            'General': {
                'Name': long_name,
                'Description': info.get('longBusinessSummary', ''),
                'UpdatedAt': datetime.now().strftime('%Y-%m-%d')
            },
            'ETF_Data': {
                'Expense_Ratio': fee if fee is not None else 0,
                'Asset_Under_Management': aum,
                'Holdings': []
            }
        }

        # Holdings from funds_data
        try:
            if hasattr(etf, 'funds_data'):
                holdings = etf.funds_data.top_holdings
                if holdings is not None and not holdings.empty:
                    for symbol, row in holdings.iterrows():
                        data['ETF_Data']['Holdings'].append({
                            'Code': symbol,
                            'Name': row.get('Name', ''),
                            'Assets_%': float(row.get('Holding Percent', 0)) * 100
                        })
        except Exception as e:
            print(f"  [WARN] Holdings error for {ticker}: {e}")

        return data
    except Exception as e:
        print(f"  [ERROR] {ticker}: {e}")
        return {}


def main():
    df = pd.read_csv(MASTER_FILE, encoding='utf-8-sig')
    etf_tickers = sorted(df[df['type'] == 'etf']['ticker'].unique().tolist())

    print(f"Building ETF cache for {len(etf_tickers)} ETFs...")
    print(f"Cache dir: {CACHE_DIR}")
    print()

    success, fail, skip = 0, 0, 0

    for i, ticker in enumerate(etf_tickers):
        cache_file = CACHE_DIR / f"{ticker}.json"

        # Skip if fresh cache exists (< 24h)
        if cache_file.exists():
            age_hours = (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() / 3600
            if age_hours < 24:
                print(f"  [{i+1}/{len(etf_tickers)}] {ticker} - SKIP (cached {age_hours:.0f}h ago)")
                skip += 1
                continue

        print(f"  [{i+1}/{len(etf_tickers)}] {ticker} - fetching...", end='', flush=True)
        data = get_etf_fundamentals_yf(ticker)

        if data and data.get('ETF_Data'):
            holdings_count = len(data['ETF_Data'].get('Holdings', []))
            aum_b = data['ETF_Data']['Asset_Under_Management'] / 1e9
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f" OK ({holdings_count} holdings, AUM=${aum_b:.1f}B)")
            success += 1
        else:
            print(f" FAILED")
            fail += 1

        time.sleep(0.5)  # Rate limiting

    print()
    print(f"Done: {success} success, {fail} failed, {skip} skipped")
    cache_count = len(list(CACHE_DIR.glob('*.json')))
    print(f"Total cache files: {cache_count}")


if __name__ == "__main__":
    main()
