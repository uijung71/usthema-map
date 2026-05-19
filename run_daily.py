"""
run_daily.py — Daily pipeline for US Theme Map
Fetches prices -> calculates returns -> git push to Streamlit Cloud
Schedule: every day 06:30 KST via Windows Task Scheduler
"""

import subprocess
import sys
import datetime
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KST = datetime.timezone(datetime.timedelta(hours=9))

# ── Telegram Config ─────────────────────────────────────────────
TG_TOKEN   = "8720582478:AAGakD7M2_-8uoGXYSTGK-fsZmJzpxBJZRU"
TG_CHAT_ID = "8356746472"


def tg(message: str):
    """Send a Telegram message (silent on failure)."""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"[TG WARN] {e}")


def now_str():
    return datetime.datetime.now(KST).strftime("%H:%M:%S")


def main():
    start = datetime.datetime.now(KST)
    date_str = start.strftime("%Y-%m-%d")
    print(f"{'='*60}")
    print(f"US Theme Map Daily Pipeline")
    print(f"Started: {start.strftime('%Y-%m-%d %H:%M:%S KST')}")
    print(f"{'='*60}")

    # ── 시작 알림 ──────────────────────────────────────────────
    tg(
        f"<b>🗺️ US 테마맵 일일 업데이트 시작</b>\n"
        f"📅 기준일: {date_str}\n"
        f"⏰ 시작: {now_str()} KST\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    # ── Step 1: 가격 수집 & 수익률 계산 ───────────────────────
    print("\n[1/2] Fetching EODHD prices & calculating returns...")
    tg(f"<b>📡 [1/2] EODHD 가격 수집 중...</b>\n⏰ {now_str()} KST")

    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "src" / "data_fetcher.py")],
            capture_output=True, text=True, check=True,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout
        print(output)
        if result.stderr:
            print("[STDERR]", result.stderr[:500])

        # Parse results from output
        success_count = "-"
        fail_count = "-"
        rows = "-"
        for line in output.splitlines():
            if "Done:" in line:
                # "[EODHD] Done: 395 success, 0 failed"
                parts = line.split()
                try:
                    success_count = parts[parts.index("success,")-1]
                    fail_count = parts[parts.index("failed")-1]
                except Exception:
                    pass
            if "returns_latest.csv" in line:
                try:
                    rows = line.split("(")[1].split(" ")[0]
                except Exception:
                    pass

        print("    [OK] Price fetch & return calculation completed.")
        tg(
            f"<b>✅ [1/2] 가격 수집 완료</b>\n"
            f"  • 성공: {success_count}개 종목\n"
            f"  • 실패: {fail_count}개\n"
            f"  • 수익률 행수: {rows}개\n"
            f"  ⏰ {now_str()} KST"
        )

    except subprocess.CalledProcessError as e:
        err_msg = (e.stderr or e.stdout or "")[:500]
        print(f"    [FAIL] Price fetch failed:\n{e.stdout}\n{e.stderr}")
        tg(
            f"<b>❌ [1/2] 가격 수집 실패!</b>\n"
            f"<pre>{err_msg}</pre>\n"
            f"⏰ {now_str()} KST"
        )
        return

    # ── Step 2: Git push ────────────────────────────────────────
    print("\n[2/2] Git push to GitHub (master branch)...")
    tg(f"<b>📤 [2/2] GitHub 업로드 중...</b>\n⏰ {now_str()} KST")

    try:
        subprocess.run(
            ["git", "add", "data/", "output/"],
            cwd=str(BASE_DIR), capture_output=True, text=True, check=True
        )
        ts = start.strftime('%Y-%m-%d %H:%M KST')
        result = subprocess.run(
            ["git", "commit", "-m", f"auto: daily theme update {ts}"],
            cwd=str(BASE_DIR), capture_output=True, text=True
        )
        if result.returncode == 0:
            subprocess.run(
                ["git", "push", "origin", "master"],
                cwd=str(BASE_DIR), capture_output=True, text=True, check=True
            )
            print("    [OK] Git push to master completed.")
            push_status = "완료"
        else:
            print("    [SKIP] Nothing new to commit.")
            push_status = "변경사항 없음 (스킵)"

    except Exception as e:
        print(f"    [WARN] Git push failed: {e}")
        push_status = f"실패: {e}"

    # ── 완료 알림 ──────────────────────────────────────────────
    elapsed = (datetime.datetime.now(KST) - start).total_seconds()
    elapsed_str = f"{int(elapsed//60)}분 {int(elapsed%60)}초"

    tg(
        f"<b>🎉 US 테마맵 업데이트 완료!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 데이터 기준일: <b>{date_str}</b>\n"
        f"✅ 가격 수집: {success_count}개 종목\n"
        f"📤 GitHub push: {push_status}\n"
        f"⏱️ 소요시간: {elapsed_str}\n"
        f"⏰ 완료: {now_str()} KST\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 https://usthema-map-jovtj2y3bgbbnmvtluubzp.streamlit.app/"
    )

    print(f"\n{'='*60}")
    print(f"Pipeline finished in {elapsed:.1f}s  ({datetime.datetime.now(KST).strftime('%H:%M:%S KST')})")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
