import streamlit as st
import pandas as pd
import os
import base64

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
# 4. 데이터 불러오기 및 화면 출력 (표 그리기)
# ==========================================
csv_path = os.path.join(current_dir, 'result.csv')
txt_path = os.path.join(current_dir, 'last_update.txt')

# 업데이트 시간 확인
try:
    with open(txt_path, 'r', encoding='utf-8') as f:
        update_time = f.read()
    st.caption(f"🕒 마지막 업데이트: {update_time}")
except:
    st.caption("🕒 업데이트 진행 중이거나 아직 데이터가 없습니다.")

# 결과 파일(CSV) 읽어서 표로 보여주기
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    if not df.empty:
        st.success(f"🎉 총 {len(df)}개의 종목이 검색되었습니다!")
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.warning("오늘은 조건에 부합하는 종목이 없습니다.")
else:
    st.info("데이터를 수집하는 중입니다. 나중에 다시 확인해주세요.")
