"""
US Stock Theme Map Dashboard
60개 투자 테마 × 420종목 실시간 테마 지도 대시보드
# Force reload
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.theme_engine import (
    get_theme_returns, get_category_returns, get_theme_detail,
    get_theme_list, load_returns, get_stock_level_data, CATEGORY_CONFIG,
    get_etf_level_data, get_theme_historical_trend
)
from src.exchange_map import get_google_finance_url

# ── Configuration ──────────────────────────────────────────────
st.set_page_config(page_title="미국주식 60대 테마지도", page_icon="🗺️", layout="wide")
BANNER_FILE = Path("assets/banner.png")

NASDAQ_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'GOOG', 'TSLA', 'META', 'AVGO', 'ASML', 'COST', 'ADBE', 'AMD', 'NFLX', 'INTC', 'CMCSA', 'PEP', 'CSCO', 'TMUS', 'QCOM', 'AMAT', 'TXN', 'ISRG', 'HON', 'INTU', 'BKNG', 'SBUX', 'MDLZ', 'GILD', 'ADP', 'ADI', 'REGN', 'VRTX', 'LRCX', 'MU', 'MELI', 'PANW', 'SNPS', 'KLAC', 'CDNS', 'PYPL', 'MAR', 'ORLY', 'CTAS', 'NXPI', 'ROP', 'CRWD', 'LULU', 'MNST', 'ADSK', 'AEP', 'TEAM', 'IDXX', 'MCHP', 'DXCM', 'FTNT', 'CPRT', 'KDP', 'KLA', 'KHC', 'PAYX', 'AZN', 'CHTR', 'PCAR', 'BKR', 'ON', 'MDB', 'TTD', 'EXC', 'CTSH', 'GEHC', 'ANSS', 'TEAM', 'ILMN', 'SIRI', 'JD', 'PDD', 'BIDU', 'NTES', 'MELI', 'DOCU', 'OKTA', 'SPLK', 'WDAY', 'TEAM', 'ADSK', 'ATVI', 'EBAY', 'DLTR', 'SGEN', 'WBA', 'MRNA', 'ALGN']


# ── CSS Injection ──────────────────────────────────────────────
def inject_css():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    [data-testid="stAppViewBlockContainer"] { max-width: 1200px; margin: auto; }
    .section-header {
        font-size: 1.65rem !important; font-weight: 800 !important;
        color: #ffffff !important;
        border-left: 4px solid #00d4ff;
        padding-left: 14px;
        margin-bottom: 25px !important; margin-top: 45px !important;
        border-bottom: none;
        text-shadow: none;
        letter-spacing: normal;
    }
    .sub-header {
        font-size: 1.65rem !important; font-weight: 800 !important;
        color: #ffffff !important;
        border-left: 4px solid #00d4ff;
        padding-left: 14px;
        margin-bottom: 25px !important; margin-top: 45px !important;
    }
    .date-info { font-size: 0.85rem; color: #888; text-align: right; margin-top: 4px; }

    /* ── Theme Heatmap Tiles ──── */
    .theme-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 8px; margin: 10px 0;
    }
    .theme-tile {
        border-radius: 12px; padding: 12px 10px;
        text-align: center; cursor: pointer;
        border: 1px solid rgba(255,255,255,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .theme-tile:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
    .tile-name { font-size: 0.82rem; font-weight: 700; color: #fff; margin-bottom: 4px;
                 white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .tile-return { font-size: 1.1rem; font-weight: 900; }
    .tile-top { font-size: 0.7rem; color: rgba(255,255,255,0.7); margin-top: 2px; }

    /* ── Category Bar Styling ──── */
    .cat-bar {
        display: flex; gap: 8px; flex-wrap: nowrap; overflow-x: auto; 
        padding: 10px 0; margin-bottom: 20px;
        scrollbar-width: none; -ms-overflow-style: none;
    }
    .cat-bar::-webkit-scrollbar { display: none; }
    
    div.stButton > button {
        border-radius: 20px;
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #ccc !important;
        padding: 6px 16px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        transition: all 0.2s !important;
        white-space: nowrap !important;
    }
    
    /* ── 1. GLOBAL CARD CONTAINER ──── */
    body .stApp [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        background: #1a1c24 !important;
        padding: 8px 12px !important;
        margin-bottom: 5px !important;
    }
    body .stApp [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    /* ── 2. THEME NAME (GOLD LINK) ──── */
    body .stApp div[data-testid="stButton"] button[kind="primary"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        min-height: unset !important;
        height: auto !important;
        width: auto !important;
        border-radius: 0 !important;
        text-align: left !important;
    }
    body .stApp div[data-testid="stButton"] button[kind="primary"] p {
        color: #FFD700 !important;
        font-weight: 950 !important;
        font-size: 1.1rem !important;
        margin: 0 !important;
    }
    body .stApp div[data-testid="stButton"] button[kind="primary"]:hover p {
        color: #ffffff !important;
        text-decoration: underline !important;
    }

    /* ── 3. ETF BOX DESIGN (DEFAULT SECONDARY) ── */
    body .stApp div[data-testid="stButton"] button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        padding: 4px 10px !important;
        height: 32px !important;
        width: 100% !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    body .stApp div[data-testid="stButton"] button[kind="secondary"] p {
        color: #ffffff !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }
    body .stApp div[data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: #FFD700 !important;
        background: rgba(255, 215, 0, 0.15) !important;
    }

    /* ── 4. REPORT LINK (SURGICAL RATIO-BASED OVERRIDE) ── */
    /* Target the 15% width column to strip the box and make it a pure link */
    body .stApp div[data-testid="stColumn"][style*="15%"] div[data-testid="stButton"] button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        margin-top: 5px !important;
        min-height: unset !important;
        height: auto !important;
        width: auto !important;
        border-radius: 0 !important;
    }
    body .stApp div[data-testid="stColumn"][style*="15%"] div[data-testid="stButton"] button[kind="secondary"] p {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    body .stApp div[data-testid="stColumn"][style*="15%"] div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: transparent !important;
    }
    body .stApp div[data-testid="stColumn"][style*="15%"] div[data-testid="stButton"] button[kind="secondary"]:hover p {
        color: #FFD700 !important;
        text-decoration: underline !important;
    }

    /* ── 5. GAP REDUCTION ──── */
    body .stApp [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] > div:nth-child(2) {
        margin-top: -16px !important;
    }

    /* ── 6. RETURN BADGE ──── */
    body .stApp .return-badge-val {
        font-weight: 900;
        font-size: 0.95rem;
        text-align: right;
        margin-top: 2px;
    }

    /* ── ETF Card Tightening ──── */
    .etf-card-container {
        background: #1a1c24;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 15px;
        padding: 0;
        margin-bottom: 20px;
        overflow: hidden;
    }
    
    /* Reduce vertical gap between elements inside Streamlit containers */
    [data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
    }

    /* ── Stock Cards ──── */
    .stock-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 10px; margin: 10px 0;
    }
    .stock-card {
        background: linear-gradient(145deg, #23273a, #1e2130);
        border-radius: 14px; padding: 14px 12px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .stock-ticker { font-size: 0.85rem; font-weight: 700; color: #00d4ff; }
    .stock-price { font-size: 1.3rem; font-weight: 800; color: #fff; margin: 4px 0; }
    .stock-return { font-size: 0.85rem; font-weight: 600; }
    .ret-up { color: #ff4b4b; }
    .ret-down { color: #4ba3ff; }

    /* ── Ranking Table ──── */
    .rank-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }

    /* ── 1. Home Root (Gold & Monumental) ──── */
    .trace.treemap text[data-unformatted*="Home"] { 
        fill: #FFD700 !important; 
        font-size: 42px !important;
        font-weight: 950 !important;
    }

    /* ── 2. Categories (Gold & Massive) ──── */
    .trace.treemap text[data-unformatted*="<b>"],
    .trace.treemap text[data-unformatted*="<b>"] tspan { 
        fill: #FFD700 !important; 
        font-weight: 900 !important;
    }

    /* ── 3. Themes & Tickers (Bold White & Large) ──── */
    .trace.treemap text:not([data-unformatted*="Home"]):not([data-unformatted*="<b>"]),
    .trace.treemap text:not([data-unformatted*="Home"]):not([data-unformatted*="<b>"]) tspan { 
        fill: #FFFFFF !important; 
        font-weight: 800 !important; 
    }
    
    /* ── Pathbar (Navigation Breadcrumbs) ──── */
    .trace.treemap text.pathbar-text {
        fill: #FFD700 !important;
        font-size: 32px !important;
        font-weight: 900 !important;
    }
    
    /* ── ETF Board Styles (Mini Heatmap Grid) ──── */
    .etf-board { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; margin-top: 15px; margin-bottom: 40px; }
    .etf-card { background: #1a1c24; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); padding: 16px; transition: transform 0.2s; }
    .etf-card:hover { transform: translateY(-3px); border-color: rgba(255, 215, 0, 0.4); box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
    .etf-card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px; margin-bottom: 15px; }
    .etf-theme-name { font-weight: 800; font-size: 1.1rem; color: #FFD700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 60%; }
    .etf-theme-return { font-weight: 800; font-size: 0.9rem; padding: 4px 10px; border-radius: 20px; color: #fff; }
    .etf-items { display: flex; gap: 10px; }
    .etf-item { flex: 1; padding: 15px 10px; border-radius: 8px; text-align: center; border: 1px solid rgba(255,255,255,0.05); box-shadow: inset 0 2px 10px rgba(0,0,0,0.2); }
    .etf-ticker { font-size: 1.3rem; font-weight: 900; color: #ffffff; margin-bottom: 6px; letter-spacing: 0.5px; }
    .etf-return { font-size: 1.15rem; font-weight: 800; color: #ffffff; }
    
    /* ── Segmented Pill Toggle (Option 1) ── */
    div[aria-label="뷰 모드"][role="radiogroup"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        padding: 5px !important;
        border-radius: 30px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        width: fit-content !important;
        margin: 5px auto 25px auto !important;
        gap: 0 !important;
    }
    div[aria-label="뷰 모드"][role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    div[aria-label="뷰 모드"][role="radiogroup"] label {
        padding: 8px 24px !important;
        margin: 0 4px !important;
        border-radius: 25px !important;
        cursor: pointer !important;
        transition: all 0.25s ease-in-out !important;
        background: transparent !important;
        border: none !important;
    }
    div[aria-label="뷰 모드"][role="radiogroup"] label p {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #b0b3c0 !important;
        margin: 0 !important;
    }
    div[aria-label="뷰 모드"][role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
    }
    div[aria-label="뷰 모드"][role="radiogroup"] label:hover p {
        color: #ffffff !important;
    }
    div[aria-label="뷰 모드"][role="radiogroup"] label[data-checked="true"],
    div[aria-label="뷰 모드"][role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #FFD700, #FFA500) !important;
        box-shadow: 0 3px 12px rgba(255, 215, 0, 0.35) !important;
    }
    div[aria-label="뷰 모드"][role="radiogroup"] label[data-checked="true"] p,
    div[aria-label="뷰 모드"][role="radiogroup"] label:has(input:checked) p {
        color: #1a1c24 !important;
        font-size: 1.1rem !important;
        font-weight: 900 !important;
    }
    
    /* ── Segmented Pill Toggles (Period & Sort) ── */
    div[aria-label="기간 설정"][role="radiogroup"],
    div[aria-label="정렬 기준"][role="radiogroup"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        background-color: rgba(255, 255, 255, 0.04) !important;
        padding: 4px !important;
        border-radius: 30px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        width: fit-content !important;
        margin: 5px auto 15px auto !important;
        gap: 0 !important;
    }
    div[aria-label="기간 설정"][role="radiogroup"] label > div:first-child,
    div[aria-label="정렬 기준"][role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    div[aria-label="기간 설정"][role="radiogroup"] label,
    div[aria-label="정렬 기준"][role="radiogroup"] label {
        padding: 6px 16px !important;
        margin: 0 2px !important;
        border-radius: 25px !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        background: transparent !important;
        border: none !important;
    }
    div[aria-label="기간 설정"][role="radiogroup"] label p,
    div[aria-label="정렬 기준"][role="radiogroup"] label p {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #b3b3b3 !important;
        margin: 0 !important;
    }
    div[aria-label="기간 설정"][role="radiogroup"] label:hover,
    div[aria-label="정렬 기준"][role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.04) !important;
    }
    div[aria-label="기간 설정"][role="radiogroup"] label:hover p,
    div[aria-label="정렬 기준"][role="radiogroup"] label:hover p {
        color: #ffffff !important;
    }
    
    /* Active cyan style for 기간 설정 */
    div[aria-label="기간 설정"][role="radiogroup"] label[data-checked="true"],
    div[aria-label="기간 설정"][role="radiogroup"] label:has(input:checked) {
        background: rgba(0, 212, 255, 0.15) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        box-shadow: 0 2px 8px rgba(0, 212, 255, 0.2) !important;
    }
    div[aria-label="기간 설정"][role="radiogroup"] label[data-checked="true"] p,
    div[aria-label="기간 설정"][role="radiogroup"] label:has(input:checked) p {
        color: #00d4ff !important;
        font-weight: 800 !important;
    }

    /* Active amber/gold style for 정렬 기준 */
    div[aria-label="정렬 기준"][role="radiogroup"] label[data-checked="true"],
    div[aria-label="정렬 기준"][role="radiogroup"] label:has(input:checked) {
        background: rgba(255, 215, 0, 0.12) !important;
        border: 1px solid rgba(255, 215, 0, 0.25) !important;
        box-shadow: 0 2px 8px rgba(255, 215, 0, 0.15) !important;
    }
    div[aria-label="정렬 기준"][role="radiogroup"] label[data-checked="true"] p,
    div[aria-label="정렬 기준"][role="radiogroup"] label:has(input:checked) p {
        color: #FFD700 !important;
        font-weight: 800 !important;
    }
    
    /* ── Mobile Responsive ──── */
    @media (max-width: 768px) {
        .theme-grid { grid-template-columns: repeat(3, 1fr); gap: 6px; }
        .tile-name { font-size: 0.72rem; }
        .tile-return { font-size: 0.95rem; }
        .stock-grid { grid-template-columns: repeat(2, 1fr); }
        .rank-grid { grid-template-columns: 1fr; }
        .cat-bar { gap: 6px; }
        .cat-chip { padding: 6px 12px; font-size: 0.8rem; }
        
        /* Abbreviate period texts on mobile */
        div[aria-label="기간 설정"][role="radiogroup"] label p {
            font-size: 0 !important;
        }
        div[aria-label="기간 설정"][role="radiogroup"] label p::after {
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            display: inline-block;
        }
        div[aria-label="기간 설정"][role="radiogroup"] label[data-checked="true"] p::after,
        div[aria-label="기간 설정"][role="radiogroup"] label:has(input:checked) p::after {
            font-weight: 800 !important;
        }
        div[aria-label="기간 설정"][role="radiogroup"] label:nth-child(1) p::after { content: "1D"; }
        div[aria-label="기간 설정"][role="radiogroup"] label:nth-child(2) p::after { content: "1W"; }
        div[aria-label="기간 설정"][role="radiogroup"] label:nth-child(3) p::after { content: "1M"; }
        div[aria-label="기간 설정"][role="radiogroup"] label:nth-child(4) p::after { content: "3M"; }
        div[aria-label="기간 설정"][role="radiogroup"] label:nth-child(5) p::after { content: "6M"; }
        div[aria-label="기간 설정"][role="radiogroup"] label:nth-child(6) p::after { content: "1Y"; }
    }
    
    /* ── K-TREND US Top Navigation Bar ──── */
    .ktrend-nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(26, 28, 36, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 10px 24px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }
    .ktrend-brand {
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        letter-spacing: 1.5px !important;
        color: #ffffff !important;
        background: linear-gradient(90deg, #ffffff, #00d4ff) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin: 0 !important;
    }
    .ktrend-nav-tabs {
        display: flex !important;
        gap: 12px !important;
    }
    .nav-tab {
        text-decoration: none !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        color: #a0b0c0 !important;
        padding: 8px 18px !important;
        border-radius: 30px !important;
        border: 1px solid transparent !important;
        transition: all 0.25s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
    }
    .nav-tab:hover {
        color: #ffffff !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    .nav-tab.active {
        color: #ffffff !important;
        background: linear-gradient(135deg, #9b59b6, #00d4ff) !important;
        border: none !important;
        box-shadow: 0 3px 15px rgba(0, 212, 255, 0.25) !important;
    }
    /* ── K-TREND US Top Navigation Bar ──── */
    /* Outer container row */
    div[data-testid="stHorizontalBlock"]:has(> div > div[data-testid="stLinkButton"]) {
        background: linear-gradient(90deg, #0d0f1a 0%, #12192b 50%, #0d0f1a 100%) !important;
        border-bottom: 1px solid rgba(0, 212, 255, 0.2) !important;
        padding: 10px 28px !important;
        margin-bottom: 0 !important;
        align-items: center !important;
    }
    /* All link buttons in nav */
    div[data-testid="stLinkButton"] a {
        display: inline-block !important;
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 50px !important;
        padding: 9px 22px !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
        color: #c8d0e0 !important;
        text-decoration: none !important;
        letter-spacing: 0.3px !important;
        transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    div[data-testid="stLinkButton"] a:hover {
        background: rgba(0, 212, 255, 0.12) !important;
        border-color: rgba(0, 212, 255, 0.4) !important;
        color: #ffffff !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2) !important;
        transform: translateY(-1px) !important;
    }
    /* Active tab - last link_button (the one for the current page) */
    div[data-testid="stColumn"]:last-child div[data-testid="stLinkButton"] a {
        background: linear-gradient(135deg, #7c3aed, #00d4ff) !important;
        border: none !important;
        color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.35), 0 0 0 1px rgba(0,212,255,0.2) !important;
        font-weight: 900 !important;
    }
    /* ── Responsive Layout Overrides ── */
    @media (max-width: 768px) {
        /* ETF 보드: 모바일에서 1열로 */
        .etf-board {
            grid-template-columns: 1fr !important;
        }
        /* 네비게이션 링크 버튼 크기 축소 */
        div[data-testid="stLinkButton"] a {
            padding: 7px 12px !important;
            font-size: 0.82rem !important;
        }
    }
    </style>""", unsafe_allow_html=True)




# ── Helper Functions ───────────────────────────────────────────
def return_color(val):
    """Get background color based on return value."""
    if pd.isna(val) or val == 0:
        return 'rgba(100,100,100,0.3)'
    intensity = min(abs(val) / 5, 1)  # Cap at 5%
    if val > 0:
        return f'rgba(255, 75, 75, {0.15 + intensity * 0.55})'   # Red for up
    return f'rgba(75, 163, 255, {0.15 + intensity * 0.55})'       # Blue for down


def return_text_class(val):
    return 'ret-up' if val >= 0 else 'ret-down'


def fmt_return(val):
    if pd.isna(val):
        return '-'
    return f"{val:+.2f}%"


# ── Render Functions ───────────────────────────────────────────
def render_category_bar(cat_df):
    """Render category summary chips as interactive buttons."""
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = '전체'
    
    with st.container():
        cols = st.columns([1] * (len(cat_df) + 1))
        
        # 1. 'All' (전체보기) Button
        with cols[0]:
            is_active = st.session_state.selected_category == '전체'
            if st.button(
                "🌐 전체보기", 
                key="cat_all", 
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_category = '전체'
                st.rerun()
        
        # 2. Category Buttons
        for i, (_, row) in enumerate(cat_df.iterrows()):
            cat = row['category']
            cfg = CATEGORY_CONFIG.get(cat, {'icon': '📦', 'color': '#aaa'})
            ret = row['avg_return']
            is_active = st.session_state.selected_category == cat
            short_name = cat.split("&")[0].strip()
            
            with cols[i+1]:
                if st.button(
                    f"{cfg['icon']} {short_name} {fmt_return(ret)}", 
                    key=f"cat_{i}", 
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.selected_category = cat
                    st.rerun()


def render_ai_report():
    """Render the AI-generated theme analysis report based on selected period."""
    import json
    from pathlib import Path
    
    report_file = Path("data/ai_reports.json")
    if not report_file.exists():
        return
        
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            reports = json.load(f)
    except Exception:
        return
        
    period_label = st.session_state.get('period', '1개월')
    # Map back Korean label to JSON key
    label_to_key = {'1일': '1d', '1주': '1w', '1개월': '1m', '3개월': '3m', '6개월': '6m', '1년': '1y'}
    key = label_to_key.get(period_label, '1m')
    
    report_text = reports.get(key, "")
    if not report_text:
        return
        
    # Render UI
    st.markdown(f'<div class="section-header">테마별 수익률 추이 상세비교</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown(report_text)


def render_theme_heatmap(return_col='avg_return', selected_cat='전체'):
    """Render theme treemap showing Category -> Theme hierarchy (no stocks at top level, stocks show when zoomed)."""
    if 'active_theme' not in st.session_state:
        st.session_state.active_theme = None
    active_theme = st.session_state.active_theme

    stocks_df = get_stock_level_data(return_col)
    if not stocks_df.empty and 'category' in stocks_df.columns:
        stocks_df['category'] = stocks_df['category'].str.replace(r'\s*\([^)]*\)', '', regex=True).str.strip()

    if stocks_df.empty:
        st.warning("표시할 데이터가 없습니다.")
        return

    if selected_cat != '전체':
        stocks_df = stocks_df[stocks_df['category'] == selected_cat]

    is_zoomed = False
    if st.session_state.active_theme:
        stocks_df = stocks_df[stocks_df['theme_name'] == st.session_state.active_theme]
        is_zoomed = True

    CATEGORY_DISPLAY_NAMES = {
        '기술 패권 & 디지털 혁신': '기술 패권',
        '에너지 주권 & 지구의 미래': '에너지 주권',
        '바이오 혁명 & 인류의 진화': '바이오 혁명',
        '신공급망 & 국가 안보': '신공급망',
        '미래 소비 & 라이프스타일': '미래 소비'
    }

    # Dynamic CSS injection based on treemap zoom state to support wrapping and large fonts
    if is_zoomed:
        st.markdown("""
        <style>
        /* ── Categories (Gold, Large in Zoomed State - targeted by alignment start) ── */
        .trace.treemap text[text-anchor="start"] tspan,
        .trace.treemap text[text-anchor="start"] { 
            font-size: 38px !important; 
            font-weight: 900 !important;
            fill: #FFD700 !important;
        }
        /* ── Stocks (White, Large & Legible in Zoomed State - targeted by alignment middle) ── */
        .trace.treemap text[text-anchor="middle"] tspan,
        .trace.treemap text[text-anchor="middle"]:not([data-unformatted*="Home"]) { 
            font-weight: 800 !important;
            fill: #FFFFFF !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        /* ── Categories (Gold, Large & Single-Line in Main View - targeted by alignment start) ── */
        .trace.treemap text[text-anchor="start"] tspan,
        .trace.treemap text[text-anchor="start"] { 
            font-size: 28px !important; 
            font-weight: 900 !important;
            fill: #FFD700 !important;
        }
        /* ── Themes (White, Large & Legible in Main View - targeted by alignment middle) ── */
        .trace.treemap text[text-anchor="middle"] tspan,
        .trace.treemap text[text-anchor="middle"]:not([data-unformatted*="Home"]) { 
            font-weight: 800 !important;
            fill: #FFFFFF !important;
        }
        </style>
        """, unsafe_allow_html=True)

    if is_zoomed or selected_cat != '전체':
        with st.container(border=True):
            col_a, col_b = st.columns([2.5, 7.5])
            with col_a:
                if st.button("전체 테마 보기", use_container_width=True):
                    st.session_state.active_theme = None
                    st.session_state.selected_category = '전체'
                    st.rerun()
            with col_b:
                if is_zoomed:
                    st.markdown(f"""
                        <div style="text-align: right; font-size: 1.05rem; font-weight: 700; color: #FFD700; margin-top: 6px; margin-right: 5px;">
                            {st.session_state.active_theme} 테마 선택됨
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="text-align: right; font-size: 1.05rem; font-weight: 700; color: #FFD700; margin-top: 6px; margin-right: 5px;">
                            {selected_cat} 대분류 선택됨
                        </div>
                    """, unsafe_allow_html=True)

    stocks_df[return_col] = stocks_df[return_col].round(2)

    ids, labels, parents, values, colors, hover_text = [], [], [], [], [], []
    root_id = "root_home"
    ids.append(root_id)
    labels.append("🏠 Home")
    parents.append("")
    
    if is_zoomed:
        # FOCUSED ZOOMED-IN VIEW: Only render the active theme's stocks and its parent category
        matching_theme = stocks_df[stocks_df['theme_name'] == active_theme]
        if not matching_theme.empty:
            cat_name = matching_theme.iloc[0]['category']
            theme_avg_ret = matching_theme[return_col].mean()
            
            values.append(matching_theme['mcap'].sum())
            colors.append(theme_avg_ret)
            
            hover_html = (
                f"<span style='font-size:16px; font-weight:800; color:#FFD700;'>🏠 홈으로 이동</span><br>"
                f"<span style='font-size:13px; color:#ffffff;'>클릭하시면 메인 지도로 돌아갑니다.</span>"
            )
            hover_text.append(hover_html)
            
            # 1. Category node (Gold, 32px)
            cat_id = f"cat|{cat_name}"
            ids.append(cat_id)
            formatted_cat_name = CATEGORY_DISPLAY_NAMES.get(cat_name, cat_name)
            labels.append(f"<b>{formatted_cat_name}</b>")
            parents.append(root_id)
            values.append(matching_theme['mcap'].sum())
            colors.append(theme_avg_ret)
            
            hover_html = (
                f"<span style='font-size:16px; font-weight:800; color:#FFD700;'>📂 {formatted_cat_name}</span><br>"
                f"<span style='font-size:13px; color:#ffffff;'>대분류: {cat_name}</span>"
            )
            hover_text.append(hover_html)
            
            # 2. Individual stocks of this theme (White, 24px) - map directly to Category node
            for _, row in matching_theme.iterrows():
                stock_id = f"stock|{cat_name}|{active_theme}|{row['ticker']}"
                ids.append(stock_id)
                labels.append(f"{row['ticker']}<br>{row[return_col]:+.2f}%")
                parents.append(cat_id)
                values.append(row['mcap'])
                colors.append(row[return_col])
                
                ret = row[return_col]
                ret_arrow = '▲' if ret > 0 else ('▼' if ret < 0 else '')
                ret_color = '#ff4b4b' if ret > 0 else ('#4ba3ff' if ret < 0 else '#888')
                hover_html = (
                    f"<span style='font-size:16px; font-weight:800; color:#ffffff;'>{row['ticker']}</span><br>"
                    f"<span style='font-size:18px; font-weight:900; color:{ret_color};'>{ret_arrow} {ret:+.2f}%</span><br>"
                    f"<span style='font-size:12px; color:#FFD700;'>🎯 {active_theme} 구성 종목</span>"
                )
                hover_text.append(hover_html)
    else:
        # FULL 60-THEME GRID VIEW
        values.append(stocks_df['mcap'].sum())
        colors.append(stocks_df[return_col].mean())
        
        hover_html = (
            f"<span style='font-size:16px; font-weight:800; color:#FFD700;'>🏠 홈으로 이동</span><br>"
            f"<span style='font-size:13px; color:#ffffff;'>클릭하시면 메인 지도로 돌아갑니다.</span>"
        )
        hover_text.append(hover_html)
        
        cat_groups = stocks_df.groupby('category')
        for cat_name, cat_df in cat_groups:
            cat_id = f"cat|{cat_name}"
            ids.append(cat_id)
            formatted_cat_name = CATEGORY_DISPLAY_NAMES.get(cat_name, cat_name)
            labels.append(f"<b>{formatted_cat_name}</b>") 
            parents.append(root_id)
            values.append(cat_df['mcap'].sum())
            colors.append(cat_df[return_col].mean())
            
            hover_html = (
                f"<span style='font-size:16px; font-weight:800; color:#FFD700;'>📂 {formatted_cat_name}</span><br>"
                f"<span style='font-size:13px; color:#ffffff;'>대분류: {cat_name}</span>"
            )
            hover_text.append(hover_html)
            
            theme_groups = cat_df.groupby('theme_name')
            for theme_name, theme_df in theme_groups:
                theme_id = f"theme|{cat_name}|{theme_name}"
                ids.append(theme_id)
                
                theme_avg_ret = theme_df[return_col].mean()
                labels.append(f"{theme_name}<br>{theme_avg_ret:+.2f}%")
                parents.append(cat_id)
                values.append(theme_df['mcap'].sum())
                colors.append(theme_avg_ret)
                
                ret_arrow = '▲' if theme_avg_ret > 0 else ('▼' if theme_avg_ret < 0 else '')
                ret_color = '#ff4b4b' if theme_avg_ret > 0 else ('#4ba3ff' if theme_avg_ret < 0 else '#888')
                hover_html = (
                    f"<span style='font-size:16px; font-weight:800; color:#ffffff;'>{theme_name}</span><br>"
                    f"<span style='font-size:18px; font-weight:900; color:{ret_color};'>{ret_arrow} {theme_avg_ret:+.2f}%</span><br>"
                    f"<span style='font-size:12px; color:#FFD700;'>📂 {cat_name}</span>"
                )
                hover_text.append(hover_html)

    fig = go.Figure(go.Treemap(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        hovertext=hover_text,
        branchvalues="total",
        tiling=dict(
            pad=4,        # Add spacing between tiles to show hierarchy
            packing="squarify"
        ),
        marker=dict(
            colors=colors,
            colorscale=[[0, "#4ba3ff"], [0.5, "#1e2130"], [1, "#ff4b4b"]],
            cmin=-5, cmax=5,
            line=dict(width=1.5, color='rgba(0,0,0,0.3)') # Darker, thicker borders
        ),
        hovertemplate="%{hovertext}<extra></extra>",
        textposition="middle center",
        insidetextfont=dict(family="Noto Sans KR", color="white", size=24),
        pathbar=dict(
            visible=True,
            thickness=45,
            textfont=dict(size=24, color="#FFD700", family="Noto Sans KR", weight="bold"),
            edgeshape="/"
        )
    ))

    st.markdown("""<style>
        div[data-testid="stButton"] > button {
            background-color: rgba(255, 215, 0, 0.1) !important;
            color: #FFD700 !important;
            border: 1px solid #FFD700 !important;
            font-weight: bold !important;
            border-radius: 8px !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #FFD700 !important;
            color: #1e2130 !important;
        }
        </style>""", unsafe_allow_html=True)

    fig.update_layout(
        margin=dict(t=50, l=10, r=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=600 if is_zoomed else 750, 
        template="plotly_dark"
    )
    fig.update_traces(
        textinfo="label", 
        selector=dict(type='treemap'),
        hoverlabel=dict(
            bgcolor="#151722",
            bordercolor="rgba(255, 215, 0, 0.4)",
            font=dict(family="Noto Sans KR", size=14, color="#ffffff")
        )
    )

    event_data = st.plotly_chart(
        fig, 
        use_container_width=True, 
        config={'displayModeBar': False},
        on_select="rerun",
        selection_mode="points",
        theme=None
    )

    if event_data and "selection" in event_data and event_data["selection"]["points"]:
        point = event_data["selection"]["points"][0]
        point_id = point.get("id", "")
        needs_rerun = False
        
        if point_id == root_id:
            if st.session_state.active_theme is not None:
                st.session_state.active_theme = None
                needs_rerun = True
            if st.session_state.get('selected_category') != '전체':
                st.session_state.selected_category = '전체'
                needs_rerun = True
        elif point_id.startswith("cat|"):
            parts = point_id.split("|")
            cat_name = parts[1]
            if st.session_state.get('selected_category') != cat_name:
                st.session_state.selected_category = cat_name
                needs_rerun = True
            if st.session_state.active_theme is not None:
                st.session_state.active_theme = None
                needs_rerun = True
        elif point_id.startswith("theme|"):
            parts = point_id.split("|")
            theme_name = parts[2]
            if st.session_state.active_theme != theme_name:
                st.session_state.active_theme = theme_name
                needs_rerun = True
        elif point_id.startswith("stock|"):
            parts = point_id.split("|")
            theme_name = parts[2]
            ticker = parts[3]
            st.session_state.last_selected_ticker = ticker
            if st.session_state.active_theme != theme_name:
                st.session_state.active_theme = theme_name
                needs_rerun = True
        if needs_rerun:
            st.rerun()

    st.markdown("""
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: 12px 15px; border-radius: 10px; border-left: 5px solid #FFD700; margin-top: 10px;">
            <span style="font-size: 14px; color: #E0E0E0;">
                💡 <b>사용 팁:</b> 지도의 <b>테마명 블록을 클릭</b>하시면 하단에 <b>상세 종목 시세, 관련 ETF 및 노션 분석 리포트</b>가 나타납니다.
            </span>
        </div>
    """, unsafe_allow_html=True)


def render_rankings(theme_df):
    """Render top/bottom theme rankings side by side."""
    top10 = theme_df.head(10)
    bot10 = theme_df.tail(10).iloc[::-1]
    
    def rank_html(df, title, icon):
        html = f'<div class="sub-header">{icon} {title}</div>'
        for i, (_, row) in enumerate(df.iterrows()):
            cls = return_text_class(row['avg_return'])
            html += (
                f'<div style="display:flex;justify-content:space-between;padding:6px 8px;'
                f'border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="color:#aaa;">{i+1}. {row["theme_name"]}</span>'
                f'<span class="{cls}" style="font-weight:700;">{fmt_return(row["avg_return"])}</span>'
                f'</div>'
            )
        return html
    
    left = rank_html(top10, '상승 TOP 10', '🔥')
    right = rank_html(bot10, '하락 TOP 10', '💧')
    st.markdown(f'<div class="rank-grid"><div>{left}</div><div>{right}</div></div>', unsafe_allow_html=True)


def render_etf_board(return_col='return_1d', selected_cat='전체', sort_by="📂 카테고리별 정렬"):
    """Render the ETF cheat-sheet board with category grouping and sorting."""
    theme_df = get_theme_returns(return_col)
    etf_df = get_etf_level_data(return_col)
    
    if theme_df.empty or etf_df.empty:
        st.warning("표시할 ETF 데이터가 없습니다.")
        return
        
    if selected_cat != '전체':
        theme_df = theme_df[theme_df['category'] == selected_cat]
        
    theme_list = theme_df.to_dict('records')
    valid_themes = [t for t in theme_list if not etf_df[etf_df['theme_id'] == t['theme_id']].empty]

    if sort_by == "📂 카테고리별 정렬":
        # Group themes by category manually to ensure separation
        cat_map = {}
        for t in valid_themes:
            cat = t['category']
            if cat not in cat_map:
                cat_map[cat] = []
            cat_map[cat].append(t)
            
        # Sort category names
        sorted_cats = sorted(cat_map.keys())
        
        for data_cat in sorted_cats:
            cat_themes = sorted(cat_map[data_cat], key=lambda x: x['avg_return'], reverse=True)
            
            # Find matching config
            cat_base_name = next((k for k in CATEGORY_CONFIG.keys() if k in data_cat or data_cat in k), None)
            cfg = CATEGORY_CONFIG.get(cat_base_name, {'icon': '📂', 'color': '#FFD700'})
            
            # Large, Clear Category Header
            st.markdown(f"""
                <div style="margin: 50px 0 25px 0; padding: 15px 20px; background: linear-gradient(90deg, {cfg['color']}33, transparent); border-left: 6px solid {cfg['color']}; border-radius: 4px;">
                    <span style="font-size: 1.8rem; margin-right: 15px;">{cfg['icon']}</span>
                    <span style="font-size: 1.6rem; font-weight: 900; color: #fff; letter-spacing: -1px;">{data_cat}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Grid
            cols_per_row = 4
            for i in range(0, len(cat_themes), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, theme_row in enumerate(cat_themes[i:i+cols_per_row]):
                    with cols[j]:
                        render_etf_card(theme_row, etf_df, return_col, i, j)
    else:
        # Flat List Sorting
        if sort_by == "🔥 수익률 높은 순":
            valid_themes = sorted(valid_themes, key=lambda x: x['avg_return'], reverse=True)
        elif sort_by == "🔤 테마 이름 순":
            valid_themes = sorted(valid_themes, key=lambda x: x['theme_name'])
            
        cols_per_row = 4
        for i in range(0, len(valid_themes), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, theme_row in enumerate(valid_themes[i:i+cols_per_row]):
                with cols[j]:
                    render_etf_card(theme_row, etf_df, return_col, i, j)


@st.dialog("📊 테마 구성 종목", width="large")
def show_theme_stocks_dialog(theme_id, theme_name, return_col):
    from src.theme_engine import get_theme_detail
    meta, stocks, etfs = get_theme_detail(theme_id)
    
    st.markdown(f"### 🎯 {theme_name} 구성 종목")
    st.info(f"이 리스트는 '{theme_name}' 테마지수를 구성하는 주요 개별 종목들입니다.")
    
    if not stocks.empty:
        # Prepare display dataframe
        display_df = stocks[['ticker', return_col]].copy()
        display_df.columns = ['티커', '수익률']
        display_df['수익률'] = display_df['수익률'].apply(fmt_return)
        
        # Sort by return (parsing from string for display)
        stocks_sorted = stocks.sort_values(by=return_col, ascending=False)
        
        cols = st.columns(2)
        half = (len(stocks_sorted) + 1) // 2
        
        for idx, (col_idx, row) in enumerate(stocks_sorted.iterrows()):
            target_col = cols[0] if idx < half else cols[1]
            ret = row[return_col]
            ret_cls = "color: #ff4b4b;" if ret > 0 else ("color: #4ba3ff;" if ret < 0 else "color: #888;")
            
            target_col.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:8px 12px; background:rgba(255,255,255,0.03); border-radius:8px; margin-bottom:5px; border-left:3px solid {'#ff4b4b' if ret > 0 else '#4ba3ff' if ret < 0 else '#888'};">
                    <span style="font-weight:700; color:#00d4ff;">{row['ticker']}</span>
                    <span style="font-weight:800; {ret_cls}">{fmt_return(ret)}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("구성 종목 정보를 불러올 수 없습니다.")


def render_etf_card(theme_row, etf_df, return_col, i, j):
    """Helper to render a theme card with clean structural targeting."""
    theme_id = theme_row['theme_id']
    theme_name = theme_row['theme_row_name'] if 'theme_row_name' in theme_row else theme_row['theme_name']
    theme_ret = theme_row['avg_return']
    theme_etfs = etf_df[etf_df['theme_id'] == theme_id]
    ret_cls = return_text_class(theme_ret)
    
    with st.container(border=True):
        # Header Row: Cols [Theme, Report, Return]
        h_cols = st.columns([0.6, 0.15, 0.25])
        with h_cols[0]:
            if st.button(theme_name, key=f"btn_theme_{theme_id}", type="primary"):
                show_theme_stocks_dialog(theme_id, theme_name, return_col)
            
        with h_cols[1]:
            if st.button("리포트", key=f"btn_rpt_{theme_id}", type="secondary", use_container_width=False):
                show_notion_dialog(theme_id, theme_name)
            
        with h_cols[2]:
            st.markdown(f'<div class="return-badge-val {ret_cls}">{fmt_return(theme_ret)}</div>', unsafe_allow_html=True)
        
        # ETF Row
        if not theme_etfs.empty:
            etf_cols = st.columns(len(theme_etfs))
            for idx, (_, etf) in enumerate(theme_etfs.iterrows()):
                eret = etf[return_col]
                with etf_cols[idx]:
                    btn_label = f"{etf['ticker']} {fmt_return(eret)}"
                    if st.button(btn_label, key=f"tkr_{theme_id}_{etf['ticker']}", type="secondary", use_container_width=True):
                        show_etf_details_dialog(etf['ticker'], theme_id, theme_name)
        


@st.dialog("📖 테마 스토리", width="large")
def show_notion_dialog(theme_id, theme_name):
    from src.notion_engine import get_notion_markdown
    st.markdown(f"## {theme_name}")
    with st.spinner("노션에서 실시간으로 데이터를 불러오는 중..."):
        md_text, youtube_url = get_notion_markdown(theme_id)
        
        if youtube_url:
            st.video(youtube_url)
            st.markdown("<hr style='border:1px solid rgba(255,255,255,0.1); margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
            
        st.markdown(md_text, unsafe_allow_html=True)


@st.dialog("📦 ETF 상세 정보", width="large")
def show_etf_details_dialog(ticker, theme_id, theme_name):
    from src.theme_engine import get_etf_details, get_stock_level_data
    with st.spinner(f"{ticker} 정보를 불러오는 중..."):
        details = get_etf_details(ticker)
        
    # Check if API returned data
    is_fallback = False
    if not details or not details.get('holdings'):
        is_fallback = True
        
        # Get theme stocks as fallback holdings
        from src.theme_engine import get_stock_level_data
        stocks_df = get_stock_level_data()
        theme_stocks = stocks_df[stocks_df['theme_id'] == theme_id].sort_values('mcap', ascending=False)
        for _, s in theme_stocks.head(10).iterrows():
            details['holdings'].append({
                'ticker': s['ticker'],
                'name': s.get('name', s['ticker']),
                'weight': 0 # We don't have weights for theme components, but we show them
            })

    st.markdown(f"### {details['full_name']}")
    
    if is_fallback:
        st.warning("⚠️ **실시간 데이터 안내**: API 권한 제한으로 인해 테마 기초지수 종목 리스트로 대체되었습니다.")

    # Basic Info Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        # If fee is 0, it's likely missing from the source, show AUM instead or something else
        if details.get('expense_ratio', 0) > 0:
            st.metric("운용 보수 (Fees)", f"{details['expense_ratio']:.2f}%")
        else:
            st.metric("운용 규모", "데이터 확인 중" if not is_fallback else "N/A")
            
    with c2:
        aum_val = details.get('aum', 0)
        aum_str = f"${aum_val/1e9:.2f}B" if aum_val > 1e9 else (f"${aum_val/1e6:.2f}M" if aum_val > 1e6 else "N/A")
        st.metric("총 자산 (AUM)", aum_str if aum_val > 0 else "N/A")
        
    with c3:
        st.metric("소속 테마", theme_name)

    st.markdown("---")
    
    # Description
    if details['description']:
        # Show as a nice box instead of expander for better visibility
        st.markdown(f"""
            <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border-left:4px solid #FFD700; margin-bottom:20px;">
                <div style="font-weight:700; color:#FFD700; margin-bottom:8px;">💡 테마 및 ETF 개요</div>
                <div style="font-size:0.95rem; line-height:1.6; color:#ddd;">{details['description'].replace('\n', '<br>')}</div>
            </div>
        """, unsafe_allow_html=True)

    # Holdings Table
    if is_fallback:
        st.markdown(f"#### 📊 '{theme_name}' 테마 핵심 구성 종목 (기초지수)")
    else:
        st.markdown("#### 📊 주요 구성 종목 (Holdings Top 10)")
        
    if details['holdings']:
        h_df = pd.DataFrame(details['holdings'])
        if is_fallback:
            h_df = h_df[['ticker', 'name']].head(10)
            h_df.columns = ['티커', '종목명']
        else:
            h_df.columns = ['티커', '종목명', '비중(%)']
        st.table(h_df)
    else:
        st.info("구성 종목 정보를 표시할 수 없습니다.")

    # External Links
    st.markdown("<br>", unsafe_allow_html=True)
    link_col1, link_col2 = st.columns(2)
    with link_col1:
        st.link_button(f"🔗 {ticker} etf.com 상세 보기", f"https://www.etf.com/{ticker}", use_container_width=True)
    with link_col2:
        st.link_button(f"🚀 Google Finance 바로가기", get_google_finance_url(ticker, is_etf=True), use_container_width=True)


# ── Main ───────────────────────────────────────────────────────
def main():
    inject_css()
    
    # K-TREND US premium top navigation bar
    nav_col1, nav_col2, nav_col3 = st.columns([2.2, 1, 1])
    with nav_col1:
        st.markdown(
            '<div style="padding:4px 0 2px 4px;">'
            '<a href="https://uijung71.github.io/usthema-map/" target="_blank" style="text-decoration:none;">'
            '<span style="font-size:1.25rem;font-weight:900;letter-spacing:2px;'
            'background:linear-gradient(90deg,#ffffff,#00d4ff);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">K-TREND</span>'
            '<span style="font-size:1.25rem;font-weight:900;color:#00d4ff;letter-spacing:2px;"> US</span>'
            '</a>'
            '<span style="font-size:0.75rem;color:#556;margin-left:10px;font-weight:500;'
            'vertical-align:middle;">by KTrend Research</span>'
            '</div>',
            unsafe_allow_html=True
        )
    with nav_col2:
        st.link_button("🏢  서학 100 지수", "https://seohak-index-vpj39neemamdaw7ptfxspm.streamlit.app/", use_container_width=True)
    with nav_col3:
        st.link_button("🗺️  미국 60대 테마", "https://usthema-map-jovtj2y3bgbbnmvtluubzp.streamlit.app/", use_container_width=True)
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    if BANNER_FILE.exists():
        st.image(str(BANNER_FILE), use_container_width=True)
    
    returns_df = load_returns()
    has_data = not returns_df.empty
    
    if 'period' not in st.session_state:
        st.session_state.period = '1개월'
    
    PERIOD_MAP = {'1일': 'return_1d', '1주': 'return_1w', '1개월': 'return_1m', '3개월': 'return_3m', '6개월': 'return_6m', '1년': 'return_1y'}
    return_col = PERIOD_MAP[st.session_state.period]
    
    # --- 1. Global View Mode Persistence ---
    q_params = st.query_params
    if 'view_mode_radio' not in st.session_state:
        st.session_state['view_mode_radio'] = "개별 주식 테마 지도"
    
    if "view" in q_params and q_params["view"] == "ETF":
        st.session_state['view_mode_radio'] = "ETF 테마 보드"

    # -------------------------------------------------------------
    
    selected_cat = st.session_state.get('selected_category', '전체')
    
    # ── Top Navigation: View Mode ──────────────────────────
    view_mode = st.radio(
        "뷰 모드", 
        ["개별 주식 테마 지도", "ETF 테마 보드"], 
        horizontal=True, 
        label_visibility="collapsed",
        key="view_mode_radio"
    )
    
    st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1); margin: 10px 0 20px 0;'>", unsafe_allow_html=True)
    
    # ── Secondary Filter: Period ──────────────────────────
    st.radio("기간 설정", list(PERIOD_MAP.keys()), key='period', horizontal=True, label_visibility="collapsed")
    
    # (return_col was pre-calculated at top)

    if view_mode == "개별 주식 테마 지도":
        header_text = "60개 주식 테마 실시간지도"
        st.markdown(f'<div class="section-header">{header_text}</div>', unsafe_allow_html=True)

        # ── Data date / update time info bar ──────────────────────────
        from datetime import timezone as _tz, timedelta as _td
        _KST = _tz(_td(hours=9))
        _data_date = "-"
        if not returns_df.empty and 'date' in returns_df.columns:
            try:
                _data_date = pd.to_datetime(returns_df['date']).max().strftime('%Y-%m-%d')
            except Exception:
                pass
        _now_kst = __import__('datetime').datetime.now(_KST).strftime('%Y-%m-%d %H:%M')
        st.markdown(
            f'<div class="date-info" style="text-align:left; margin:-8px 0 10px 2px; font-size:0.85rem; color:#888;">'
            f'데이터 기준일: <span style="color:#00d4ff; font-weight:700;">{_data_date}</span>'
            f'&nbsp;|&nbsp;업데이트: <span style="color:#9b59b6; font-weight:700;">{_now_kst}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        # ───────────────────────────────────────────────────────────────

        st.info("💡 지도의 테마 블록을 클릭하시면 하단에 실시간 상세 리포트와 구성 종목 시세가 나타납니다.")

        render_theme_heatmap(return_col, selected_cat)
        
        # --- AI Theme Analysis Report ---
        if not st.session_state.get('active_theme'):
            render_ai_report()
            
        # --- Theme Details Section (Option B Inline Details Panel) ---
        active_theme = st.session_state.get('active_theme')
        if active_theme:
            # Find the theme_id matching active_theme
            theme_df_all = get_theme_returns(return_col)
            matching_theme = theme_df_all[theme_df_all['theme_name'] == active_theme]
            if not matching_theme.empty:
                theme_id = matching_theme.iloc[0]['theme_id']
                theme_avg_ret = matching_theme.iloc[0]['avg_return']
                
                # Fetch details using get_theme_detail
                meta, theme_stocks, theme_etfs = get_theme_detail(theme_id)

                # ── Header ────────────────────────────────────────────────
                st.markdown(f"""
                    <div style="margin: 40px 0 20px 0; padding: 15px 20px; background: linear-gradient(90deg, rgba(255, 215, 0, 0.15), transparent); border-left: 6px solid #FFD700; border-radius: 8px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px;">
                        <div style="display: flex; align-items: center;">
                            <span style="font-size: clamp(1.4rem, 6vw, 2.2rem); margin-right: 15px;">🎯</span>
                            <span style="font-size: clamp(1.3rem, 5.5vw, 2.0rem); font-weight: 950; color: #fff; letter-spacing: -1.5px; line-height: 1.2; word-break: keep-all;">{active_theme} 테마 상세 분석</span>
                        </div>
                        <span style="font-size: clamp(1.3rem, 5vw, 1.8rem); font-weight: 900; color: {'#ff4b4b' if theme_avg_ret >= 0 else '#4ba3ff'}; white-space: nowrap;">{fmt_return(theme_avg_ret)}</span>
                    </div>
                """, unsafe_allow_html=True)

                # ── Notion에서 YouTube URL + 텍스트 가져오기 ─────────────
                from src.notion_engine import get_notion_markdown
                with st.spinner("테마 스토리 로딩 중..."):
                    md_text, youtube_url = get_notion_markdown(theme_id)

                # ── 2-컬럼 레이아웃: 왼쪽=영상, 오른쪽=종목+ETF ─────────
                ALL_PERIODS = {
                    '1일': 'return_1d', '1주': 'return_1w', '1개월': 'return_1m',
                    '3개월': 'return_3m', '6개월': 'return_6m', '1년': 'return_1y'
                }
                col_left, col_right = st.columns([1.15, 0.85])

                with col_left:
                    st.markdown('<div style="font-size:1.05rem; font-weight:900; color:#e8eaf0; margin-bottom:10px;">🎬 테마 스토리</div>', unsafe_allow_html=True)
                    if youtube_url:
                        st.video(youtube_url)
                        
                        # Add summary text below video
                        if md_text:
                            summary_lines = [p.strip() for p in md_text.split('\n\n') if p.strip() and not p.strip().startswith('#') and not p.strip().startswith('!') and not p.strip().startswith('[')]
                            if summary_lines:
                                summary_text = " ".join(summary_lines)
                                if len(summary_text) > 350:
                                    summary_text = summary_text[:350] + "..."
                                summary_text = summary_text.replace('**', '')
                                
                                html_content = (
                                    f'<div style="margin-top:12px; padding:20px 24px; background:rgba(255,255,255,0.02); '
                                    f'border-radius:12px; border:1px solid rgba(255,255,255,0.05); min-height:240px;">'
                                    f'<div style="font-size:1.0rem; font-weight:800; color:#e8eaf0; margin-bottom:12px;">💡 핵심 요약</div>'
                                    f'<div style="font-size:0.95rem; color:#a0b0c0; line-height:1.7;">{summary_text}</div>'
                                    f'</div>'
                                )
                                st.markdown(html_content, unsafe_allow_html=True)
                    else:
                        # 준비중 플레이스홀더
                        st.markdown("""
                            <div style="
                                aspect-ratio: 16/9;
                                background: linear-gradient(135deg, #1a1f2e, #12192b);
                                border: 1px dashed rgba(0,212,255,0.25);
                                border-radius: 14px;
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                justify-content: center;
                                gap: 12px;
                                margin-bottom: 8px;
                            ">
                                <div style="font-size:2.5rem;">🎬</div>
                                <div style="font-size:1.05rem; font-weight:800; color:#a0b0c0;">테마 영상 준비 중</div>
                                <div style="font-size:0.82rem; color:#556; text-align:center; padding:0 20px;">
                                    노션 페이지에 YouTube 영상을 추가하면<br>이 자리에 자동으로 표시됩니다.
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    # ── ① 기간별 수익률 스코어보드 ────────────────────────
                    st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:1.05rem; font-weight:900; color:#e8eaf0; margin-bottom:10px;">📈 기간별 평균 수익률</div>', unsafe_allow_html=True)
                    if not theme_stocks.empty:
                        score_html = (
                            '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(70px, 1fr)); '
                            'gap:6px; margin-bottom:8px;">'
                        )
                        for period_label, period_col in ALL_PERIODS.items():
                            avg_r = theme_stocks[period_col].mean() if period_col in theme_stocks.columns else 0
                            p_color  = '#ff4b4b' if avg_r > 0 else ('#4ba3ff' if avg_r < 0 else '#888')
                            p_arrow  = '▲' if avg_r > 0 else ('▼' if avg_r < 0 else '–')
                            is_active = (period_label == st.session_state.period)
                            a_bg  = 'linear-gradient(135deg,rgba(0,212,255,0.18),rgba(124,58,237,0.12))' if is_active else 'rgba(255,255,255,0.04)'
                            a_bd  = 'rgba(0,212,255,0.5)' if is_active else 'rgba(255,255,255,0.07)'
                            a_lbl = '#00d4ff' if is_active else '#5a6480'
                            score_html += (
                                f'<div style="background:{a_bg}; border:1px solid {a_bd}; '
                                f'border-radius:12px; padding:10px 4px; text-align:center;">'
                                f'<div style="font-size:0.72rem; color:{a_lbl}; font-weight:700; margin-bottom:4px;">{period_label}</div>'
                                f'<div style="font-size:1.0rem; font-weight:900; color:{p_color}; letter-spacing:-0.5px;">{p_arrow}{abs(avg_r):.1f}%</div>'
                                f'</div>'
                            )
                        score_html += '</div>'
                        st.markdown(score_html, unsafe_allow_html=True)

                with col_right:
                    # ── ② 구성 종목 카드 (2열, 큰 텍스트) ─────────────────
                    if not theme_stocks.empty:
                        stocks_sorted = theme_stocks.sort_values(by=return_col, ascending=False)
                        up_cnt   = int((stocks_sorted[return_col] > 0).sum())
                        dn_cnt   = int((stocks_sorted[return_col] < 0).sum())
                        flat_cnt = int((stocks_sorted[return_col] == 0).sum())

                        # 섹션 라벨 + 상승/하락 배지
                        badge_flat = (
                            f'<span style="font-size:0.82rem; background:rgba(255,255,255,0.07); '
                            f'color:#888; border-radius:50px; padding:3px 10px; font-weight:700;">– {flat_cnt}</span>'
                        ) if flat_cnt else ''
                        st.markdown(
                            f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">'
                            f'<span style="font-size:1.05rem; font-weight:900; color:#e8eaf0;">📊 구성 종목</span>'
                            f'<span style="font-size:0.82rem; background:rgba(255,75,75,0.18); color:#ff4b4b; '
                            f'border-radius:50px; padding:3px 10px; font-weight:800; margin-left:8px;">▲ {up_cnt}</span>'
                            f'<span style="font-size:0.82rem; background:rgba(75,161,255,0.18); color:#4ba3ff; '
                            f'border-radius:50px; padding:3px 10px; font-weight:800;">▼ {dn_cnt}</span>'
                            f'{badge_flat}'
                            f'<span style="font-size:0.78rem; color:#3a4255; margin-left:auto;">{st.session_state.period} 기준</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                        def sync_period_from_pills():
                            pill_key = f"theme_pill_{active_theme}_{st.session_state.period}"
                            new_val = st.session_state.get(pill_key)
                            if new_val:
                                st.session_state.period = new_val

                        # 기간 인터랙티브 연동 (Pills)
                        st.pills(
                            "기간 연동", 
                            options=list(ALL_PERIODS.keys()), 
                            default=st.session_state.period, 
                            key=f"theme_pill_{active_theme}_{st.session_state.period}", 
                            label_visibility="collapsed",
                            on_change=sync_period_from_pills
                        )
                        st.markdown('<div style="margin-bottom:4px;"></div>', unsafe_allow_html=True)

                        # 2열 카드 그리드 -> 반응형 1~2열 카드 그리드
                        cards_html = '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:20px; margin-bottom:20px;">'
                        for _, row in stocks_sorted.iterrows():
                            ret   = row[return_col]
                            close = row.get('close', None)
                            color = '#ff4b4b' if ret > 0 else ('#4ba3ff' if ret < 0 else '#888')
                            arrow = '▲' if ret > 0 else ('▼' if ret < 0 else '–')
                            g_url = get_google_finance_url(row['ticker'], is_etf=False)
                            price_html = (
                                f'<div style="font-size:0.82rem; color:#6b7485; font-weight:500; margin-top:1px;">'
                                f'${close:,.2f}</div>'
                            ) if (close and close > 0) else ''
                            cards_html += (
                                f'<a href="{g_url}" target="_blank" style="text-decoration:none;">'
                                f'<div style="'
                                f'background:linear-gradient(145deg,#1a1f2e,#13182a);'
                                f'border:1px solid rgba(255,255,255,0.07);'
                                f'border-top:2px solid {color};'
                                f'border-radius:10px; padding:11px 14px;'
                                f'display:flex; justify-content:space-between; align-items:center;">'
                                f'<div>'
                                f'<div style="font-size:1.05rem; font-weight:900; color:#00d4ff; letter-spacing:0.3px;">{row["ticker"]}</div>'
                                f'{price_html}'
                                f'</div>'
                                f'<div style="text-align:right;">'
                                f'<div style="font-size:1.15rem; font-weight:900; color:{color};">'
                                f'{arrow}{abs(ret):.1f}%</div>'
                                f'</div>'
                                f'</div></a>'
                            )
                        cards_html += '</div>'
                        st.markdown(cards_html, unsafe_allow_html=True)
                    else:
                        st.info("구성 종목 정보가 없습니다.")

                    # ── ③ 관련 ETF — 통합 카드 (버튼 내장) ──────────────
                    st.markdown(
                        '<div style="font-size:1.05rem; font-weight:900; color:#e8eaf0; '
                        'margin-bottom:10px;">📦 관련 ETF</div>',
                        unsafe_allow_html=True
                    )
                    if not theme_etfs.empty:
                        for _, etf in theme_etfs.iterrows():
                            eret    = etf[return_col]
                            e_color = '#ff4b4b' if eret > 0 else ('#4ba3ff' if eret < 0 else '#888')
                            e_arrow = '▲' if eret > 0 else ('▼' if eret < 0 else '–')

                            ecol1, ecol2 = st.columns([2.5, 1.2], vertical_alignment="center")
                            with ecol1:
                                st.markdown(
                                    f'<div style="background:linear-gradient(145deg,#1a1f2e,#13182a); '
                                    f'border:1px solid rgba(255,255,255,0.08); '
                                    f'border-left:4px solid {e_color}; '
                                    f'border-radius:10px; padding:8px 16px; '
                                    f'display:flex; justify-content:space-between; align-items:center;">'
                                    f'<span style="font-size:1.25rem; font-weight:900; color:#00d4ff; letter-spacing:1px;">{etf["ticker"]}</span>'
                                    f'<span style="font-size:1.2rem; font-weight:900; color:{e_color};">{e_arrow}&nbsp;{abs(eret):.2f}%</span>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                            with ecol2:
                                if st.button(f"📋 상세 분석", key=f"active_theme_etf_{etf['ticker']}", use_container_width=True):
                                    show_etf_details_dialog(etf['ticker'], theme_id, active_theme)
                            
                            st.markdown('<div style="margin-bottom:6px;"></div>', unsafe_allow_html=True)
                    else:
                        st.info("등록된 관련 ETF가 없습니다.")



        
        theme_df_all = get_theme_returns(return_col)
        theme_df = theme_df_all.copy()
        if selected_cat != '전체':
            theme_df = theme_df[theme_df['category'] == selected_cat]
            
        st.markdown('<br><div class="sub-header">테마 수익률 누적 추이</div>', unsafe_allow_html=True)
        st.info(f"💡 현재 선택된 **{st.session_state.period}** 기간 동안의 누적 수익률 흐름입니다.")
        
        all_themes_in_view = theme_df['theme_name'].tolist() if not theme_df.empty else get_theme_list()['theme_name'].tolist()
        
        if active_theme and active_theme in all_themes_in_view:
            default_sel = [active_theme]
        else:
            default_sel = all_themes_in_view[:3] if len(all_themes_in_view) >= 3 else all_themes_in_view
            
        selected_trend_themes = st.multiselect("비교할 테마를 선택하세요 (다중 선택 가능):", options=all_themes_in_view, default=default_sel, label_visibility="collapsed")
        
        if selected_trend_themes:
            trend_df = get_theme_historical_trend(selected_trend_themes, return_col)
            if trend_df is not None and not trend_df.empty:
                fig_trend = px.line(
                    trend_df, 
                    x='date', 
                    y='value', 
                    color='theme_name', 
                    labels={'theme_name': '테마명', 'value': '누적 수익률 (%)', 'date': '날짜'},
                    markers=True if len(trend_df)/len(selected_trend_themes) < 20 else False
                )
                fig_trend.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", 
                    paper_bgcolor="rgba(0,0,0,0)", 
                    font=dict(color="#ffffff", size=13), 
                    margin=dict(t=10, b=20, l=40, r=20), 
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)", title=""), 
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)", zeroline=True, zerolinecolor="rgba(255,255,255,0.5)"), 
                    legend=dict(title_text='', orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("📊 선택한 테마의 추이 데이터를 불러올 수 없습니다. 데이터 수집 상태를 확인해주세요.")
        
        if not theme_df_all.empty:
            period_str = st.session_state.get('period', '1개월')
            st.markdown(f'<div class="section-header">테마랭킹</div>', unsafe_allow_html=True)
            render_rankings(theme_df_all)

        # Bottom section only for Stock Map mode
        st.markdown("<br><hr style='border:1px solid rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">60대 테마 살펴보기</div>', unsafe_allow_html=True)
        cat_df = get_category_returns(return_col)
        if not cat_df.empty:
            render_category_bar(cat_df)
        st.markdown("<br>", unsafe_allow_html=True)
        
        theme_df_all = get_theme_returns(return_col)
        if selected_cat != '전체':
            theme_df_all = theme_df_all[theme_df_all['category'] == selected_cat]
        st.markdown(f'<div class="sub-header">ETF 목록 (총 {len(theme_df_all)}개 테마)</div>', unsafe_allow_html=True)
        theme_df_all = theme_df_all.sort_values(by='theme_id', ascending=True)
        themes = list(theme_df_all['theme_name'])
        cols_per_row = 4
        for i in range(0, len(themes), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, theme in enumerate(themes[i:i+cols_per_row]):
                with cols[j]:
                    if st.button(f" {theme}", use_container_width=True, key=f"btn_rep_{theme}", type="tertiary"):
                        t_id = theme_df_all[theme_df_all['theme_name'] == theme].iloc[0]['theme_id']
                        show_notion_dialog(t_id, theme)
    else:
        # ETF Board View
        header_text = "ETF 테마 보드"
        st.markdown(f'<div class="section-header">{header_text}</div>', unsafe_allow_html=True)
        st.info("💡 카드의 우측 상단은 해당 테마의 '주식 평균 수익률'입니다. 리포트 버튼을 통해 상세 내용을 확인하세요.")
        
        cat_df = get_category_returns(return_col)
        if not cat_df.empty:
            st.markdown('<p style="font-size:0.85rem; color:#888; margin-bottom:5px; text-align:center;">📋 카테고리 필터</p>', unsafe_allow_html=True)
            render_category_bar(cat_df)
        
        sel_col1, sel_col2 = st.columns(2)
        with sel_col1:
            st.info("💡 카테고리를 선택하시면 하위 테마와 ETF 리스트를 볼 수 있습니다.")
        with sel_col2:
            sort_by = st.radio("정렬 기준", ["📂 카테고리별 정렬", "🔥 수익률 높은 순", "🔤 테마 이름 순"], horizontal=True, label_visibility="collapsed")

        render_etf_board(return_col, selected_cat, sort_by=sort_by)


if __name__ == "__main__":
    main()
