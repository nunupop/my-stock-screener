import streamlit as st
import pandas as pd
import os
import base64
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 1. 페이지 기본 설정
st.set_page_config(page_title="나스닥 N자형 돌파 검색", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'bg.jpg')

# 배경 이미지 및 테이블 글씨/테두리 최적화 CSS 설정
if os.path.exists(image_path):
    img_base64 = get_base64_of_bin_file(image_path)
    st.markdown(
        f"""
        <style>
        /* 기본 앱 배경 설정 */
        .stApp {{
            background-image: url("data:image/jpeg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* 💡 테이블 컨테이너 영역 */
        [data-testid="stDataFrame"] {{
            background-color: #0B0B0C !important;
            border-radius: 10px;
            padding: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }}
        
        /* 💡 스트림릿 내장 데이터 그리드 테마 변수 강제 오버라이드 (가장 확실한 방법) */
        [data-testid="stDataFrame"] > div {{
            --style-background: #0B0B0C !important;
            --style-text-main: #FFFFFF !important;
            --style-text-medium: #E0E0E0 !important;
            --style-text-light: #A0A0A0 !important;
            --style-border-light: rgba(255, 255, 255, 0.15) !important;
            --style-border-medium: rgba(255, 255, 255, 0.25) !important;
            --style-accent-color: #29b5e8 !important;
        }}
        
        /* 테이블 내부 요소들 글씨색 흰색으로 강제 고정 */
        [data-testid="stDataFrame"] th, 
        [data-testid="stDataFrame"] td, 
        [data-testid="stDataFrame"] span, 
        [data-testid="stDataFrame"] div[role="gridcell"] {{
            color: #FFFFFF !important;
        }}
        
        /* 링크(차트 바로가기) 색상 활성화 */
        [data-testid="stDataFrame"] a {{
            color: #29b5e8 !important;
            text-decoration: none;
        }}
        [data-testid="stDataFrame"] a:hover {{
            text-decoration: underline;
        }}
        
        /* st.success 알림창 내부의 글씨 색상을 회색으로 */
        div[data-testid="stNotification"] p {{
            color: #CCCCCC !important;
            font-weight: 500;
        }}
        
        header{{visibility:hidden;}}
        .stDeployButton{{display:none;}}
        footer{{visibility:hidden;}}
        .block-container{{
          padding-top: 0rem !important;
          padding-bottom: 0rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 타이틀
st.markdown(
    """
    <div style='margin-bottom: 20px;'>
        <div style='text-align: center; font-size: 35px; font-weight: bold; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>
            🇺🇸 오늘의 NASDAQ <br> 눌림목 돌파 종목
        </div>
        <div style='text-align: right; font-size: 14px; color: #E0E0E0; font-style: italic; margin-top: 10px;'>
            by Mr.CHOI
        </div>
    </div>
    """, 
    unsafe_allow_html=True
)

# 나스닥 전용 데이터 경로 설정
csv_path = os.path.join(current_dir, 'result_nasdaq.csv')
txt_path = os.path.join(current_dir, 'last_update_nasdaq.txt')

# 마지막 업데이트 시간 표시
try:
    with open(txt_path, 'r', encoding='utf-8') as f:
        update_time = f.read()
    st.markdown(f"<p style='color: #E0E0E0;'>🕒 마지막 업데이트(KST): {update_time}</p>", unsafe_allow_html=True)
except:
    st.markdown("<p style='color: #E0E0E0;'>🕒 업데이트 진행 중이거나 아직 데이터가 없습니다.</p>", unsafe_allow_html=True)

# 3. 데이터 로드 및 표 생성
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    if not df.empty:
        st.success(f"🎉 총 {len(df)}개의 나스닥 종목이 검색되었습니다!")
        
        # 티커 대문자 변환 및 야후 파이낸스 링크 생성
        df['종목코드'] = df['종목코드'].astype(str).str.upper()
        df['야후차트'] = "https://finance.yahoo.com/quote/" + df['종목코드']
        
        # 컬럼 순서 및 표기명 정리
        display_df = df
