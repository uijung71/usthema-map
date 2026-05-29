"""
generate_ai_report.py
Fetches theme-level returns for 6 periods and calls Anthropic Claude API to generate a narrative report.
Saves the result to data/ai_reports.json.
"""

import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Import our theme aggregation logic
from theme_engine import get_category_returns, get_theme_returns

load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "data" / "ai_reports.json"

# The 6 periods we support in the Treemap
PERIODS = {
    '1d': 'return_1d',
    '1w': 'return_1w',
    '1m': 'return_1m',
    '3m': 'return_3m',
    '6m': 'return_6m',
    '1y': 'return_1y'
}

PERIOD_KO = {
    '1d': '1일', '1w': '1주', '1m': '1개월', 
    '3m': '3개월', '6m': '6개월', '1y': '1년'
}

def build_prompt(period_key: str, period_label: str) -> str:
    """Builds the prompt string containing the data for the given period."""
    return_col = PERIODS[period_key]
    
    # 1. Get Category (Super-Sector) Performance
    cat_df = get_category_returns(return_col)
    if cat_df.empty:
        return ""
        
    cat_text = "== 대분류(Super Sector) 수익률 ==\n"
    for _, row in cat_df.iterrows():
        cat_text += f"- {row['category']}: {row['avg_return']:.2f}%\n"
        
    # 2. Get Top and Bottom Themes
    theme_df = get_theme_returns(return_col)
    if theme_df.empty:
        return ""
        
    theme_df = theme_df.dropna(subset=['avg_return'])
    top_themes = theme_df.head(5)
    bottom_themes = theme_df.tail(3)
    
    theme_text = "\n== 상승률 상위 TOP 5 테마 ==\n"
    for _, row in top_themes.iterrows():
        theme_text += f"- {row['theme_name']} ({row['category']}): {row['avg_return']:.2f}% (대장주: {row['top_ticker']} {row['top_return']:.2f}%)\n"

    theme_text += "\n== 하락률 하위 TOP 3 테마 ==\n"
    for _, row in bottom_themes.iterrows():
        theme_text += f"- {row['theme_name']} ({row['category']}): {row['avg_return']:.2f}%\n"

    system_prompt = f"""당신은 월스트리트의 수석 퀀트 애널리스트입니다.
주어진 미국 주식 테마의 '{period_label}' 단위 수익률 데이터를 바탕으로 전문가 수준의 시황 분석 리포트를 작성해야 합니다.

[작성 지침]
1. 인사말이나 불필요한 서론/결론 없이 바로 본론 3가지 항목만 마크다운으로 출력하세요.
2. 어투는 전문적이고 단호한 증권사 리포트 형식(~입니다, ~가 특징입니다, ~전망됩니다)을 사용하세요.
3. 숫자를 나열하지 말고, 자금의 흐름(Money Move)과 섹터 로테이션의 '원인과 맥락'을 추론하여 내러티브를 부여하세요.
4. 반드시 다음 3단락 구조를 지켜주세요:

### 🔥 주도 섹터 분석
(가장 자금이 강하게 쏠린 대분류와 핵심 테마의 특징 요약)

### 🔍 자금 이동 및 특이 동향
(상승장 속 소외된 테마, 차익실현 징후, 또는 급등한 신흥 테마 포착)

### 💡 투자 인사이트
(이 데이터 흐름을 바탕으로 앞으로 주목해야 할 흐름 또는 리스크)
"""

    user_prompt = f"다음은 {period_label} 동안의 미국 주식 테마 수익률 데이터입니다.\n\n{cat_text}{theme_text}"
    return system_prompt, user_prompt


def generate_report_claude(system_prompt: str, user_prompt: str) -> str:
    """Calls Anthropic Claude API using requests."""
    if not CLAUDE_API_KEY:
        return "CLAUDE_API_KEY가 .env 파일에 설정되지 않았습니다."
        
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 2500,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }
    
    response = None
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"].strip()
    except Exception as e:
        print(f"[Error] API Call failed: {e}")
        if response is not None and hasattr(response, 'text'):
            print(f"Details: {response.text}")
        return f"API 호출 중 오류가 발생했습니다: {e}"


def run():
    print("Starting AI Theme Report Generation...")
    reports = {}
    
    for key, col in PERIODS.items():
        period_label = PERIOD_KO[key]
        print(f"Generating report for {period_label}...")
        
        system_p, user_p = build_prompt(key, period_label)
        if not user_p:
            reports[key] = "데이터가 부족하여 리포트를 생성할 수 없습니다."
            continue
            
        report_text = generate_report_claude(system_p, user_p)
        reports[key] = report_text
        print(f" -> Completed {len(report_text)} chars.")
        
    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    print(f"Saved all reports to {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
