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
    """Send a single Telegram message (silent on failure)."""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"[TG WARN] {e}")


def main():
    start = datetime.datetime.now(KST)
    date_str = start.strftime("%Y-%m-%d")

    print(f"{'='*60}")
    print(f"US Theme Map Daily Pipeline")
    print(f"Started: {start.strftime('%Y-%m-%d %H:%M:%S KST')}")
    print(f"{'='*60}")

    # ── 결과 추적용 변수 ────────────────────────────────────────
    step1_ok     = False
    step1_detail = ""
    step15_ok    = False
    step15_detail = ""
    step2_ok     = False
    step2_detail = ""

    # ── Step 1: 가격 수집 & 수익률 계산 ───────────────────────
    print("\n[1/2] Fetching EODHD prices & calculating returns...")
    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "src" / "data_fetcher.py")],
            capture_output=True, text=True, check=True,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout
        print(output)

        # Parse counts from stdout
        success_count, fail_count, rows = "-", "-", "-"
        for line in output.splitlines():
            if "Done:" in line:
                parts = line.split()
                try:
                    success_count = parts[parts.index("success,")-1]
                    fail_count    = parts[parts.index("failed")-1]
                except Exception:
                    pass
            if "returns_latest.csv" in line:
                try:
                    rows = line.split("(")[1].split(" ")[0]
                except Exception:
                    pass

        step1_ok     = True
        step1_detail = f"종목 {success_count}개 수집 / 실패 {fail_count}개 / 수익률 {rows}행"
        print("    [OK] Completed.")

    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "")[:200]
        step1_detail = err
        print(f"    [FAIL] {err}")

    # ── Step 1.5: AI 리포트 자동 생성 ────────────────────────
    print("\n[1.5/2] Generating AI Theme Reports...")
    if step1_ok:
        try:
            result_ai = subprocess.run(
                [sys.executable, str(BASE_DIR / "src" / "generate_ai_report.py")],
                cwd=str(BASE_DIR), capture_output=True, text=True, check=True,
                encoding='utf-8', errors='replace'
            )
            print(result_ai.stdout)
            step15_ok = True
            step15_detail = "AI 리포트 (6개 기간) 생성 완료"
            print("    [OK] AI Reports Generated.")
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or "")[:200]
            step15_detail = f"생성 실패: {err}"
            print(f"    [FAIL] {err}")
    else:
        step15_detail = "Step 1 실패로 스킵"
        print("    [SKIP] Skipped due to Step 1 failure.")

    # ── Step 2: Git push ────────────────────────────────────────
    print("\n[2/2] Git push to GitHub (master)...")
    if step1_ok:
        try:
            subprocess.run(
                ["git", "add", "data/", "output/"],
                cwd=str(BASE_DIR), capture_output=True, text=True, check=True
            )
            ts = start.strftime('%Y-%m-%d %H:%M KST')
            commit_result = subprocess.run(
                ["git", "commit", "-m", f"auto: daily theme update {ts}"],
                cwd=str(BASE_DIR), capture_output=True, text=True
            )
            if commit_result.returncode == 0:
                subprocess.run(
                    ["git", "push", "origin", "master"],
                    cwd=str(BASE_DIR), capture_output=True, text=True, check=True
                )
                step2_ok     = True
                step2_detail = "master 브랜치 push 완료"
                print("    [OK] Git push completed.")
            else:
                step2_ok     = True
                step2_detail = "변경사항 없음 (commit 스킵)"
                print("    [SKIP] Nothing to commit.")
        except Exception as e:
            step2_detail = str(e)[:200]
            print(f"    [WARN] Git push failed: {e}")
    else:
        step2_detail = "Step 1 실패로 스킵"
        print("    [SKIP] Skipped due to Step 1 failure.")

    # ── 최종 완료 텔레그램 (한 번만) ───────────────────────────
    elapsed  = (datetime.datetime.now(KST) - start).total_seconds()
    end_time = datetime.datetime.now(KST).strftime("%H:%M KST")
    elapsed_str = f"{int(elapsed//60)}분 {int(elapsed%60)}초"

    s1_icon = "✅" if step1_ok else "❌"
    s2_icon = "✅" if step2_ok else "❌"
    all_ok  = step1_ok and step2_ok

    tg(
        f"<b>{'🎉' if all_ok else '⚠️'} US 테마맵 일일 업데이트 결과</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{s1_icon} <b>Step 1</b> 가격 수집\n"
        f"    {step1_detail}\n\n"
        f"{'✅' if step15_ok else '❌'} <b>Step 1.5</b> AI 리포트\n"
        f"    {step15_detail}\n\n"
        f"{s2_icon} <b>Step 2</b> GitHub Push\n"
        f"    {step2_detail}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 기준일: <b>{date_str}</b>\n"
        f"⏱️ 소요: {elapsed_str}  |  완료: {end_time}"
    )

    print(f"\n{'='*60}")
    print(f"Pipeline finished in {elapsed:.1f}s  ({end_time})")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
