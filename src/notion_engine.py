import streamlit as st
import os
from notion_client import Client

# 임시 매핑 딕셔너리 (fallback용)
THEME_NOTION_MAP = {
    1: "2f866277921980d68545fa2c4dfecf7c",
    2: "2ff6627792198040ad94e5a153aeb36a",
    3: "302662779219802ea0dad2c913fdee2e",
    4: "30c662779219804d9610df12b1f0fc6c",
    5: "30f66277921980b9846ee1c1084daebf",
    6: "32066277921980ddb3b3e5e8c375cba0",
    7: "3206627792198030a2ebf1175854cdbf",
    8: "32066277921980fc83f5e89915c8653f",
    9: "33b662779219812bbef7d1281baa0f88",
    10: "33b66277921981c9bfe0f40092c2d51a",
    11: "33b66277921981579f26d335d0470d0a",
    12: "33b66277921981a292f5c2b9f1b9a686",
    13: "33b662779219810aa4e3e80a7583fa23",
    14: "33b662779219816fad4dcea1e1a35425",
    15: "33c6627792198174aac6e49b2c3a62fd",
    16: "33e662779219817d909de6a924463620",
    17: "35066277921981549bbfcfa8fc7907f2",
    18: "35066277921981e8aee3cd49da84f0ac",
    19: "3506627792198177928dd1eb25fdd14f",
    20: "350662779219804ab0ccf5077020a552",
    21: "358662779219815f811bfc5e96e0b7ba",
    22: "35866277921981f9bf92fdf306e552ad",
    23: "3586627792198141891cc0b2c138525b",
    # Task-71에서 추출한 새로운 페이지 ID들 (Fallback)
    24: "3646627792198153aa92ff41460c4331",
    25: "3676627792198177b0f0f344d4d6465f",
    26: "368662779219811189f3dccf3d74cb93",
    27: "368662779219818bab3ac059f631b2fe",
    28: "36866277921981fc82cccc64b9839e77",
    29: "368662779219814280b0df8885b4b167",
    30: "36966277921981d08959e4655a2d2a74",
    31: "369662779219819c94dccdf63907bbe2",
    32: "36b66277921981e0829cc5df238af95d",
    33: "36b6627792198154b7a9c2ff60115f3c",
    34: "36b66277921981609ca7fe6c7b118623",
    35: "36b66277921981ec83c5f35f259c8872",
    36: "36b6627792198187b7f8d5a57ba929e0",
    37: "36b66277921981f48f0ce566ae165a68",
    38: "36b66277921981cfa9f1cd115b44980a",
    39: "36b66277921981f585c4e1125006115b"
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_dynamic_theme_map(token: str) -> dict:
    import re
    base_map = THEME_NOTION_MAP.copy()
    try:
        client = Client(auth=token)
        # Search all pages
        res = client.search(filter={"property": "object", "value": "page"})
        pages = res.get('results', [])
        
        dynamic_map = {}
        for p in pages:
            title = ""
            if 'properties' in p:
                for prop_name, prop_data in p['properties'].items():
                    if prop_data.get('type') == 'title':
                        title_arr = prop_data.get('title', [])
                        if title_arr:
                            title = title_arr[0].get('plain_text', '')
                        break
            
            # Extract number before "테마" or just the first number if it looks like a theme page
            match = re.search(r'(\d+)\s*테마', title)
            if not match:
                # Some titles might just be "1. AI"
                match = re.search(r'^\[?(\d+)\]?\s*(?:\.|:|테마|theme)', title)
            
            if match:
                theme_id = int(match.group(1))
                if 1 <= theme_id <= 200:
                    dynamic_map[theme_id] = p['id'].replace('-', '')
        
        base_map.update(dynamic_map)
        return base_map
    except Exception as e:
        print(f"Error fetching dynamic map: {e}")
        return base_map

def parse_rich_text(rich_text_arr):
    out = ""
    for rt in rich_text_arr:
        text = rt.get("plain_text", "")
        if rt.get("annotations", {}).get("bold"):
            text = f"**{text}**"
        if rt.get("annotations", {}).get("italic"):
            text = f"*{text}*"
        if rt.get("annotations", {}).get("code"):
            text = f"`{text}`"
        if rt.get("href"):
            text = f"[{text}]({rt['href']})"
        out += text
    return out

def extract_youtube_url(blocks):
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
    try:
        try:
            token = st.secrets.get("NOTION_TOKEN", "")
        except FileNotFoundError:
            token = ""
            
        if not token:
            error_msg = "⚠️ **노션 API 연동 대기 중입니다.**\n\n1. 노션 개발자 센터에서 API 키를 발급받으세요.\n2. `.streamlit/secrets.toml` 파일에 `NOTION_TOKEN = \"시크릿키\"`를 입력하세요.\n3. 노션 페이지 우측 상단 '공유'에서 API를 초대하세요."
            return error_msg, None
            
        os.environ['NOTION_TOKEN'] = token
        
        dynamic_map = get_dynamic_theme_map(token)
        page_id = dynamic_map.get(theme_id)
        
        if not page_id:
            return f"이 테마(ID: {theme_id})에 대한 노션 페이지가 아직 연결되지 않았습니다. 메인 페이지에 리포트가 추가되었는지 확인해 주세요.", None
            
        if "notion.site/" in page_id or "notion.so/" in page_id:
            page_id = page_id.split("-")[-1].split("?")[0]
            
        client = Client(auth=token)
        res = client.blocks.children.list(block_id=page_id)
        blocks = res.get('results', [])
        
        while res.get('has_more'):
            res = client.blocks.children.list(block_id=page_id, start_cursor=res['next_cursor'])
            blocks.extend(res.get('results', []))
            
        youtube_url = extract_youtube_url(blocks)
        md_text = blocks_to_markdown(blocks, youtube_url)
        
        return md_text, youtube_url
    except Exception as e:
        error_msg = f"⚠️ **노션 데이터를 불러오는 중 오류가 발생했습니다.**\n\n페이지가 API와 공유되지 않았거나 ID가 잘못되었을 수 있습니다.\n\n`(에러: {str(e)})`"
        return error_msg, None
