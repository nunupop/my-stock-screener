import streamlit as st
import pandas as pd
import os
import base64
import FinanceDataReader as fdr  # 차트 데이터를 불러오기 위해 추가!
from datetime import datetime, timedelta  # 날짜 계산을 위해 추가!

# 1. 페이지 기본 설정 (가장 먼저 와야 합니다)
st.set_page_config(page_title="볼린저 밴드 돌파 검색", layout="wide")

# ==========================================
# 2. 배경 이미지 설정 (도화지 깔기)
# ==========================================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'bg.jpg') # 내 컴퓨터/깃허브에 있는 이미지 파일명

if os.path.exists(image_path):
    img_base64 = get_base64_of_bin_file(image_path)
    st.markdown(
        f"""
        <style>
        /* 배경 이미지 꽉 차게 설정 */
        .stApp {{
            background-image: url("data:image/jpeg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* 표(데이터프레임)를 어두운 배경에서 잘 보이게 코팅 */
        .stDataFrame {{
            background-color: rgba(0, 0, 0, 0.6) !important;
            border-radius: 10px;
            padding: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# 3. 타이틀 텍스트 설정 (글씨 쓰기)
# ==========================================
st.markdown(
    """
    <div style='margin-bottom: 30px;'>
        <div style='text-align: center; font-size: 45px; font-weight: bold; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>
            📈 오늘의 KOSPI <br> 돌파 종목
        </div>
        <div style='text-align: right; font-size: 22px; color: #E0E0E0; font-style: italic; margin-top: 10px;'>
            by Mr.CHOI
        </div>
    </div>
    """, 
    unsafe_allow_html=True
)

# ==========================================
# 4. 데이터 불러오기 및 화면 출력 (차트 기능 포함)
# ==========================================
csv_path = os.path.join(current_dir, 'result.csv')
txt_path = os.path.join(current_dir, 'last_update.txt')

# 업데이트 시간 확인
try:
    with open(txt_path, 'r', encoding='utf-8') as f:
        update_time = f.read()
    # 글씨가 어두운 배경에서 잘 보이도록 하얀색 텍스트로 감쌌습니다.
    st.markdown(f"<p style='color: #E0E0E0;'>🕒 마지막 업데이트: {update_time}</p>", unsafe_allow_html=True)
except:
    st.markdown("<p style='color: #E0E0E0;'>🕒 업데이트 진행 중이거나 아직 데이터가 없습니다.</p>", unsafe_allow_html=True)

# 결과 파일(CSV) 읽어서 표로 보여주기
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    if not df.empty:
        st.success(f"🎉 총 {len(df)}개의 종목이 검색되었습니다!")
        
        # [추가] 종목코드를 6자리 문자열로 변환 (예: 5930 -> 005930)
        df['종목코드'] = df['종목코드'].astype(str).str.zfill(6)
        
        # [추가] 표에 네이버 증권 바로가기 링크 생성
        df['네이버차트'] = "https://finance.naver.com/item/main.naver?code=" + df['종목코드']
        
        # [수정] 링크를 클릭할 수 있는 형태로 표 그리기
        st.dataframe(
            df,
            column_config={
                "네이버차트": st.column_config.LinkColumn("차트 바로가기", display_text="네이버 차트 📈")
            },
            width='stretch', 
            hide_index=True
        )
        
        st.markdown("---")
        
        # ==========================================
        # 5. 앱 내 미니 차트 출력 구역
        # ==========================================
        st.markdown("<h3 style='color: white; text-shadow: 1px 1px 2px black;'>📊 화면에서 바로 차트 확인하기</h3>", unsafe_allow_html=True)
        
        # 검색된 종목들의 이름으로 선택 박스(드롭다운) 만들기
        stock_list = df['종목명'].tolist()
        selected_stock_name = st.selectbox("종목을 선택하세요:", stock_list)
        
        if selected_stock_name:
            # 선택한 종목의 코드 찾기
            selected_code = df[df['종목명'] == selected_stock_name]['종목코드'].values[0]
            
            # 해당 종목의 최근 120일 데이터 불러오기 (미니 차트용)
            start_date = datetime.now() - timedelta(days=120)
            chart_df = fdr.DataReader(selected_code, start_date)
            
            if not chart_df.empty:
                # 화면에 종가 기준 선 차트 그리기
                st.line_chart(chart_df['Close'])
                
    else:
        st.warning("오늘은 조건에 부합하는 종목이 없습니다.")
else:
    st.info("데이터를 수집하는 중입니다. 나중에 다시 확인해주세요.")
