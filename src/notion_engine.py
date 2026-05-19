import streamlit as st
import os
from notion_client import Client

# 임시 매핑 딕셔너리 (추후 theme_master.csv 등으로 분리 가능)
THEME_NOTION_MAP = {
    1: "2f866277921980d68545fa2c4dfecf7c",  # AI & 데이터 지능
    2: "2ff6627792198040ad94e5a153aeb36a",  # 반도체 하드웨어
    3: "302662779219802ea0dad2c913fdee2e",  # 로봇 & 자동화
    4: "30c662779219804d9610df12b1f0fc6c",  # 사이버 보안
    5: "30f66277921980b9846ee1c1084daebf",  # 클라우드 & 소프트웨어
    6: "32066277921980ddb3b3e5e8c375cba0",  # 디지털 금융
    7: "3206627792198030a2ebf1175854cdbf",  # 블록체인 & 디지털 자산
    8: "32066277921980fc83f5e89915c8653f",  # 게임 & 메타버스
    9: "33b662779219812bbef7d1281baa0f88",  # AI 수익화
    10: "33b66277921981c9bfe0f40092c2d51a", # 양자 컴퓨터
    11: "33b66277921981579f26d335d0470d0a", # 디지털 트윈
    12: "33b66277921981a292f5c2b9f1b9a686", # RWA 토큰화
    13: "33b662779219810aa4e3e80a7583fa23", # AI 엣지 디바이스
    14: "33b662779219816fad4dcea1e1a35425", # 반도체 패키징
    15: "33c6627792198174aac6e49b2c3a62fd", # 스마트 시티
    16: "33e662779219817d909de6a924463620", # 데이터 프라이버시
    17: "35066277921981549bbfcfa8fc7907f2", # AI 가상 비서
    18: "35066277921981e8aee3cd49da84f0ac", # 반도체 설계 소프트웨어
    19: "3506627792198177928dd1eb25fdd14f", # 차세대 원자력
    20: "350662779219804ab0ccf5077020a552", # 청정 에너지
    21: "358662779219815f811bfc5e96e0b7ba", # 기후 변화
    22: "35866277921981f9bf92fdf306e552ad", # 전력망 인프라
    23: "3586627792198141891cc0b2c138525b", # 구리 & 희토류
}

def parse_rich_text(rich_text_arr):
    out = ""
    for rt in rich_text_arr:
        text = rt.get("plain_text", "")
        # Apply annotations
        if rt.get("annotations", {}).get("bold"):
            text = f"**{text}**"
        if rt.get("annotations", {}).get("italic"):
            text = f"*{text}*"
        if rt.get("annotations", {}).get("code"):
            text = f"`{text}`"
        
        # Apply link
        if rt.get("href"):
            text = f"[{text}]({rt['href']})"
        out += text
    return out

def extract_youtube_url(blocks):
    """
    Scans blocks to find the first YouTube URL.
    """
    for b in blocks:
        b_type = b.get("type")
        if not b_type:
            continue
        url = None
        if b_type == "video":
            video = b.get("video", {})
            v_type = video.get("type")
            if v_type == "external":
                url = video.get("external", {}).get("url")
            elif v_type == "file":
                url = video.get("file", {}).get("url")
        elif b_type == "embed":
            url = b.get("embed", {}).get("url")
        elif b_type == "bookmark":
            url = b.get("bookmark", {}).get("url")
            
        if url and ("youtube.com" in url or "youtu.be" in url):
            return url
    return None

def blocks_to_markdown(blocks, youtube_url=None):
    md = ""
    for b in blocks:
        b_type = b["type"]
        
        # Skip this block if it contains the extracted youtube_url
        url = None
        if b_type == "video":
            video = b.get("video", {})
            v_type = video.get("type")
            if v_type == "external":
                url = video.get("external", {}).get("url")
            elif v_type == "file":
                url = video.get("file", {}).get("url")
        elif b_type == "embed":
            url = b.get("embed", {}).get("url")
        elif b_type == "bookmark":
            url = b.get("bookmark", {}).get("url")
            
        if url and youtube_url and url == youtube_url:
            continue
            
        if b_type == "paragraph":
            md += parse_rich_text(b["paragraph"]["rich_text"]) + "\n\n"
        elif b_type == "heading_1":
            md += "# " + parse_rich_text(b["heading_1"]["rich_text"]) + "\n\n"
        elif b_type == "heading_2":
            md += "## " + parse_rich_text(b["heading_2"]["rich_text"]) + "\n\n"
        elif b_type == "heading_3":
            md += "### " + parse_rich_text(b["heading_3"]["rich_text"]) + "\n\n"
        elif b_type == "bulleted_list_item":
            md += "- " + parse_rich_text(b["bulleted_list_item"]["rich_text"]) + "\n"
        elif b_type == "numbered_list_item":
            md += "1. " + parse_rich_text(b["numbered_list_item"]["rich_text"]) + "\n"
        elif b_type == "quote":
            md += "> " + parse_rich_text(b["quote"]["rich_text"]) + "\n\n"
        elif b_type == "divider":
            md += "---\n\n"
    return md

@st.cache_data(ttl=3600, show_spinner=False)
def get_notion_markdown(theme_id: int):
    """
    Fetches a Notion page, extracts the first YouTube URL, and converts the rest to Markdown.
    Returns: (md_text, youtube_url)
    """
    try:
        try:
            token = st.secrets.get("NOTION_TOKEN", "")
        except FileNotFoundError:
            token = ""
            
        # Check if token exists
        if not token:
            error_msg = "⚠️ **노션 API 연동 대기 중입니다.**\n\n1. 노션 개발자 센터에서 API 키를 발급받으세요.\n2. `.streamlit/secrets.toml` 파일에 `NOTION_TOKEN = \"시크릿키\"`를 입력하세요.\n3. 노션 페이지 우측 상단 '공유'에서 API를 초대하세요."
            return error_msg, None
            
        os.environ['NOTION_TOKEN'] = token
        
        # Check if theme_id exists in map
        page_id = THEME_NOTION_MAP.get(theme_id)
        if not page_id:
            return f"이 테마(ID: {theme_id})에 대한 노션 페이지가 아직 연결되지 않았습니다.", None
            
        # Extract ID if a full URL was accidentally passed
        if "notion.site/" in page_id or "notion.so/" in page_id:
            page_id = page_id.split("-")[-1].split("?")[0]
            
        client = Client(auth=token)
        
        # Fetch blocks directly using notion_client
        res = client.blocks.children.list(block_id=page_id)
        blocks = res.get('results', [])
        
        # Fetch more blocks if paginated (up to 100 per page normally)
        while res.get('has_more'):
            res = client.blocks.children.list(block_id=page_id, start_cursor=res['next_cursor'])
            blocks.extend(res.get('results', []))
            
        youtube_url = extract_youtube_url(blocks)
        md_text = blocks_to_markdown(blocks, youtube_url)
        
        return md_text, youtube_url
    except Exception as e:
        error_msg = f"⚠️ **노션 데이터를 불러오는 중 오류가 발생했습니다.**\n\n페이지가 API와 공유되지 않았거나 ID가 잘못되었을 수 있습니다.\n\n`(에러: {str(e)})`"
        return error_msg, None
