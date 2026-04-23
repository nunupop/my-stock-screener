import streamlit as st
import pandas as pd
import os
import base64
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 1. 페이지 기본 설정
st.set_page_config(page_title="볼린저 밴드 돌파 검색", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'bg.jpg')

if os.path.exists(image_path):
    img_base64 = get_base64_of_bin_file(image_path)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .stDataFrame {{
            background-color: rgba(0, 0, 0, 0.6) !important;
            border-radius: 10px;
            padding: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

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

csv_path = os.path.join(current_dir, 'result.csv')
txt_path = os.path.join(current_dir, 'last_update.txt')

try:
    with open(txt_path, 'r', encoding='utf-8') as f:
        update_time = f.read()
    st.markdown(f"<p style='color: #E0E0E0;'>🕒 마지막 업데이트: {update_time}</p>", unsafe_allow_html=True)
except:
    st.markdown("<p style='color: #E0E0E0;'>🕒 업데이트 진행 중이거나 아직 데이터가 없습니다.</p>", unsafe_allow_html=True)

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    if not df.empty:
        st.success(f"🎉 총 {len(df)}개의 종목이 검색되었습니다!")
        
        df['종목코드'] = df['종목코드'].astype(str).str.zfill(6)
        df['네이버차트'] = "https://finance.naver.com/item/main.naver?code=" + df['종목코드']
        
        st.dataframe(
            df,
            column_config={
                "네이버차트": st.column_config.LinkColumn("차트 바로가기", display_text="네이버 차트 📈")
            },
            width='stretch', 
            hide_index=True
        )
        
        st.markdown("---")
        
        st.markdown("<h3 style='color: white; text-shadow: 1px 1px 2px black;'>📊 화면에서 바로 차트 확인하기</h3>", unsafe_allow_html=True)
        
        stock_list = df['종목명'].tolist()
        selected_stock_name = st.selectbox("종목을 선택하세요:", stock_list)
        
        if selected_stock_name:
            selected_code = df[df['종목명'] == selected_stock_name]['종목코드'].values[0]
            entry_price = df[df['종목명'] == selected_stock_name]['진입가'].values[0]
            
            start_date = datetime.now() - timedelta(days=200)
            chart_df = fdr.DataReader(selected_code, start_date)
            
            if not chart_df.empty:
                chart_df['ma20'] = chart_df['Close'].rolling(window=20).mean()
                chart_df['std20'] = chart_df['Close'].rolling(window=20).std(ddof=0)
                chart_df['upper'] = chart_df['ma20'] + 2 * chart_df['std20']
                chart_df['lower'] = chart_df['ma20'] - 2 * chart_df['std20']
                
                chart_df = chart_df.iloc[-100:]
                
                fig = go.Figure()
                
                # 캔들 차트
                fig.add_trace(go.Candlestick(
                    x=chart_df.index,
                    open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'], close=chart_df['Close'],
                    name='일봉 캔들'
                ))
                
                # 볼린저 밴드 상단
                fig.add_trace(go.Scatter(
                    x=chart_df.index, y=chart_df['upper'], 
                    line=dict(color='rgba(255, 0, 0, 0.5)', width=1.5, dash='dot'), 
                    name='BB 상단'
                ))
                
                # 볼린저 밴드 하단
                fig.add_trace(go.Scatter(
                    x=chart_df.index, y=chart_df['lower'], 
                    line=dict(color='rgba(0, 0, 255, 0.5)', width=1.5, dash='dot'), 
                    name='BB 하단',
                    fill='tonexty',
                    fillcolor='rgba(128, 128, 128, 0.1)'
                ))
                
                # 돌파 기준가
                fig.add_hline(
                    y=entry_price, line_dash="solid", line_color="green", line_width=2,
                    annotation_text=f"돌파 기준가 ({entry_price:,.0f}원)", 
                    annotation_position="top left",
                    annotation_font=dict(color="green", size=14, weight="bold")
                )

                # 👇 [수정된 부분] yaxis_title 삭제 및 가격축 오른쪽 이동 👇
                fig.update_layout(
                    title=f"<b>{selected_stock_name}</b> 일봉(Daily) 볼린저 밴드 돌파 차트",
                    # yaxis_title='주가 (원)',  <-- 눈에 거슬리던 이 줄을 지워버렸습니다!
                    yaxis=dict(
                        side="right",     # 💡 가격 숫자를 오른쪽으로 보냅니다 (HTS 스타일)
                        tickformat=","    # 💡 숫자에 천 단위 콤마(,)를 찍어줍니다
                    ),
                    xaxis=dict(
                        rangeslider=dict(visible=False),
                        rangebreaks=[dict(bounds=["sat", "mon"])]
                    ),
                    template='plotly_white',
                    height=550,
                    margin=dict(l=50, r=50, t=50, b=50),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.15,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
    else:
        st.warning("오늘은 조건에 부합하는 종목이 없습니다.")
else:
    st.info("데이터를 수집하는 중입니다. 나중에 다시 확인해주세요.")
