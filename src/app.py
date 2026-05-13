"""
US Stock Theme Map Dashboard
60개 투자 테마 × 420종목 실시간 테마 지도 대시보드
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
    get_theme_list, load_returns, CATEGORY_CONFIG,
)

# ── Configuration ──────────────────────────────────────────────
st.set_page_config(page_title="미국주식 60대 테마지도", page_icon="🗺️", layout="wide")
BANNER_FILE = Path("assets/banner.png")


# ── CSS Injection ──────────────────────────────────────────────
def inject_css():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    * { font-family: 'Noto Sans KR', sans-serif !important; }
    [data-testid="stAppViewBlockContainer"] { max-width: 1200px; margin: auto; }
    .section-header {
        font-size: 1.8rem; font-weight: 900; margin: 30px 0 15px 0;
        background: linear-gradient(90deg, #00d4ff, #9b59b6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sub-header { font-size: 1.2rem; font-weight: 700; color: #ddd; margin: 10px 0 8px 0; }
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

    /* ── Category Bar ──── */
    .cat-bar {
        display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0 20px 0;
        justify-content: center;
    }
    .cat-chip {
        padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: 700;
        border: 1px solid rgba(255,255,255,0.15);
        background: rgba(255,255,255,0.05);
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

    /* ── Mobile Responsive ──── */
    @media (max-width: 768px) {
        .theme-grid { grid-template-columns: repeat(3, 1fr); gap: 6px; }
        .tile-name { font-size: 0.72rem; }
        .tile-return { font-size: 0.95rem; }
        .stock-grid { grid-template-columns: repeat(2, 1fr); }
        .rank-grid { grid-template-columns: 1fr; }
        .cat-bar { gap: 6px; }
        .cat-chip { padding: 6px 12px; font-size: 0.8rem; }
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
    """Render category summary chips."""
    chips = ''
    for _, row in cat_df.iterrows():
        cat = row['category']
        cfg = CATEGORY_CONFIG.get(cat, {'icon': '📦', 'color': '#aaa'})
        ret = row['avg_return']
        cls = 'ret-up' if ret >= 0 else 'ret-down'
        chips += (
            f'<div class="cat-chip" style="border-color:{cfg["color"]}40;">'
            f'{cfg["icon"]} {cat.split("&")[0].strip()} '
            f'<span class="{cls}">{fmt_return(ret)}</span></div>'
        )
    st.markdown(f'<div class="cat-bar">{chips}</div>', unsafe_allow_html=True)


def render_theme_heatmap(theme_df, return_col='avg_return'):
    """Render 60-theme heatmap grid."""
    tiles = ''
    for _, row in theme_df.iterrows():
        ret = row[return_col] if not pd.isna(row[return_col]) else 0
        bg = return_color(ret)
        cls = return_text_class(ret)
        top_info = f"{row.get('top_ticker', '')}" if pd.notna(row.get('top_ticker')) else ''
        tiles += (
            f'<div class="theme-tile" style="background:{bg};">'
            f'<div class="tile-name">{row["theme_name"]}</div>'
            f'<div class="tile-return {cls}">{fmt_return(ret)}</div>'
            f'<div class="tile-top">🏆 {top_info}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="theme-grid">{tiles}</div>', unsafe_allow_html=True)


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


def render_theme_detail(theme_id):
    """Render detailed view for a specific theme."""
    meta, stocks, etfs = get_theme_detail(theme_id)
    if meta is None:
        st.warning("테마 정보를 찾을 수 없습니다.")
        return
    
    cfg = CATEGORY_CONFIG.get(meta['category'], {'icon': '📦', 'color': '#aaa'})
    st.markdown(
        f'<div class="section-header">{cfg["icon"]} {meta["theme_name"]}</div>'
        f'<div class="date-info">대분류: {meta["category"]}</div>',
        unsafe_allow_html=True,
    )
    
    # Stock cards
    st.markdown('<div class="sub-header">📊 주식 종목</div>', unsafe_allow_html=True)
    cards = ''
    for _, row in stocks.iterrows():
        ret = row.get('return_1d', 0) if 'return_1d' in row.index else 0
        ret = ret if not pd.isna(ret) else 0
        close = row.get('close', 0) if 'close' in row.index else 0
        close = close if not pd.isna(close) else 0
        cls = return_text_class(ret)
        cards += (
            f'<div class="stock-card">'
            f'<div class="stock-ticker">{row["ticker"]}</div>'
            f'<div class="stock-price">${close:,.2f}</div>'
            f'<div class="stock-return {cls}">{fmt_return(ret)}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="stock-grid">{cards}</div>', unsafe_allow_html=True)
    
    # ETF cards
    if not etfs.empty:
        st.markdown('<div class="sub-header">📦 관련 ETF</div>', unsafe_allow_html=True)
        etf_cards = ''
        for _, row in etfs.iterrows():
            ret = row.get('return_1d', 0) if 'return_1d' in row.index else 0
            ret = ret if not pd.isna(ret) else 0
            close = row.get('close', 0) if 'close' in row.index else 0
            close = close if not pd.isna(close) else 0
            cls = return_text_class(ret)
            etf_cards += (
                f'<div class="stock-card">'
                f'<div class="stock-ticker">{row["ticker"]}</div>'
                f'<div class="stock-price">${close:,.2f}</div>'
                f'<div class="stock-return {cls}">{fmt_return(ret)}</div>'
                f'</div>'
            )
        st.markdown(f'<div class="stock-grid">{etf_cards}</div>', unsafe_allow_html=True)


# ── Main ───────────────────────────────────────────────────────
def main():
    inject_css()
    
    # Banner
    if BANNER_FILE.exists():
        st.image(str(BANNER_FILE), use_container_width=True)
    
    # Load data
    returns_df = load_returns()
    has_data = not returns_df.empty
    
    # Period selector in session state
    if 'period' not in st.session_state:
        st.session_state.period = '1일'
    
    PERIOD_MAP = {'1일': 'return_1d', '1주': 'return_1w', '1개월': 'return_1m', '3개월': 'return_3m'}
    
    # Navigation
    page = st.sidebar.radio("📍 페이지", ["🗺️ 테마 지도", "🔍 테마 상세"])
    
    if page == "🗺️ 테마 지도":
        st.markdown('<div class="section-header">🗺️ 미국주식 60대 테마 실시간 지도</div>', unsafe_allow_html=True)
        
        if not has_data:
            st.warning("⚠️ 시세 데이터가 없습니다. `python src/data_fetcher.py`를 먼저 실행하세요.")
            st.info("데모 모드: 테마 구조만 표시됩니다.")
        
        # Period selector
        with st.expander("⚙️ 기간 설정"):
            st.selectbox("수익률 기준", list(PERIOD_MAP.keys()), key='period')
        
        return_col = PERIOD_MAP[st.session_state.period]
        
        # Category summary
        st.markdown('<div class="sub-header">📋 대분류별 요약</div>', unsafe_allow_html=True)
        cat_df = get_category_returns(return_col)
        if not cat_df.empty:
            render_category_bar(cat_df)
        
        # Theme heatmap
        st.markdown(f'<div class="sub-header">🗺️ 60개 테마 히트맵 ({st.session_state.period} 수익률)</div>', unsafe_allow_html=True)
        theme_df = get_theme_returns(return_col)
        if not theme_df.empty:
            render_theme_heatmap(theme_df)
            
            # Rankings
            st.markdown('<div class="sub-header">📊 테마 랭킹</div>', unsafe_allow_html=True)
            render_rankings(theme_df)
        else:
            # Show empty theme grid from master
            from src.theme_engine import load_master
            master = load_master()
            themes = master[['theme_id', 'theme_name', 'category']].drop_duplicates()
            tiles = ''
            for _, row in themes.iterrows():
                tiles += (
                    f'<div class="theme-tile" style="background:rgba(100,100,100,0.2);">'
                    f'<div class="tile-name">{row["theme_name"]}</div>'
                    f'<div class="tile-return" style="color:#888;">-</div>'
                    f'<div class="tile-top">데이터 대기중</div>'
                    f'</div>'
                )
            st.markdown(f'<div class="theme-grid">{tiles}</div>', unsafe_allow_html=True)
    
    elif page == "🔍 테마 상세":
        theme_list = get_theme_list()
        if theme_list.empty:
            st.error("테마 데이터를 찾을 수 없습니다.")
            return
        
        # Theme selector
        options = {f"{row['theme_id']}. {row['theme_name']}": row['theme_id'] 
                   for _, row in theme_list.iterrows()}
        selected = st.sidebar.selectbox("테마 선택", list(options.keys()))
        theme_id = options[selected]
        
        render_theme_detail(theme_id)


if __name__ == "__main__":
    main()
