"""
run_daily.py — Daily pipeline for US Theme Map
Fetches prices → calculates returns → git push to Streamlit Cloud
"""

import subprocess
import sys
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    start = datetime.datetime.now()
    print(f"{'='*60}")
    print(f"US Theme Map Daily Pipeline - {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Step 1: Fetch prices & calculate returns
    print("\n[1/2] Fetching EODHD prices...")
    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "src" / "data_fetcher.py")],
            capture_output=True, text=True, check=True,
            encoding='utf-8', errors='replace'
        )
        print(result.stdout)
        print("    [OK] Price fetch completed.")
    except subprocess.CalledProcessError as e:
        print(f"    [FAIL] Price fetch failed: {e.stderr}")
        return
    
    # Step 2: Git push
    print("\n[2/2] Git push to GitHub...")
    try:
        subprocess.run(["git", "add", "data/", "output/"], cwd=str(BASE_DIR),
                        capture_output=True, text=True, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", f"auto: daily update {start.strftime('%Y-%m-%d %H:%M')}"],
            cwd=str(BASE_DIR), capture_output=True, text=True
        )
        if result.returncode == 0:
            subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR),
                            capture_output=True, text=True, check=True)
            print("    [OK] Git push completed.")
        else:
            print("    [SKIP] Nothing to commit.")
    except Exception as e:
        print(f"    [WARN] Git push failed: {e}")
    
    elapsed = (datetime.datetime.now() - start).total_seconds()
    print(f"\n{'='*60}")
    print(f"Pipeline completed in {elapsed:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
