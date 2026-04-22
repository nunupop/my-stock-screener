import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="볼린저 밴드 돌파 검색", layout="wide")
st.markdown(
    """
    <div style='text-align: center; margin-bottom: 20px;'>
        <span style='font-size: 40px; font-weight: bold;'>📈 오늘의 KOSPI</span> <br>
        <span style='font-size: 40px; font-weight: bold;'>돌파 종목</span> <br>
        <span style='font-size: 25px; color: gray;'>by Mr.CHOI</span>
    </div>
    """, 
    unsafe_allow_html=True
)

# 현재 실행 중인 파이썬 파일의 진짜 폴더 위치 알아내기
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, 'result.csv')
txt_path = os.path.join(current_dir, 'last_update.txt')

# 업데이트 시간 확인
try:
    with open(txt_path, 'r', encoding='utf-8') as f:
        update_time = f.read()
    st.caption(f"🕒 마지막 업데이트: {update_time}")
except:
    st.caption("🕒 업데이트 진행 중이거나 아직 데이터가 없습니다.")

# 데이터 불러오기
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    if not df.empty:
        st.success(f"🎉 총 {len(df)}개의 종목이 검색되었습니다!")
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.warning("오늘은 조건에 부합하는 종목이 없습니다.")
else:
    st.info("데이터를 수집하는 중입니다. 나중에 다시 확인해주세요.")
