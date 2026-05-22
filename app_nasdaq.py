import streamlit as st
import pandas as pd
import os
import base64
import FinanceDataReader as fdr
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

st.markdown(
    """
    <div style='margin-bottom: 30px;'>
        <div style='text-align: center; font-size: 35px; font-weight: bold; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>
            🇺🇸 오늘의 NASDAQ <br> N자형 눌림목 돌파 종목
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
    st.markdown(f"<p style='color: #E0E0E0;'>🕒 마지막 업데이트(KST): {update_time}</p>", unsafe_allow_html=True)
except:
    st.markdown("<p style='color: #E0E0E0;'>🕒 업데이트 진행 중이거나 아직 데이터가 없습니다.</p>", unsafe_allow_html=True)

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    if not df.empty:
        st.success(f"🎉 총 {len(df)}개의 나스닥 종목이 검색되었습니다!")
        
        # 💡 미국 주식은 6자리 자릿수 채우기(zfill)가 필요 없으므로 대문자 변환만 처리
        df['종목코드'] = df['종목코드'].astype(str).str.upper()
        # 💡 네이버 금융 대신 야후 파이낸스 연결
        df['야후차트'] = "https://finance.yahoo.com/quote/" + df['종목코드']
        
        st.dataframe(
            df,
            column_config={
                "야후차트": st.column_config.LinkColumn("차트 바로가기", display_text="Yahoo Finance 📈")
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
            
            # 💡 120일 이평선 선행 계산을 위해 기간을 300일로 넉넉하게 확장
            start_date = datetime.now() - timedelta(days=300)
            chart_df = fdr.DataReader(selected_code, start_date)
            
            if not chart_df.empty:
                # 💡 볼린저 밴드 대신 N자형 패턴 이평선(5, 20, 60, 120) 계산
                chart_df['ma5'] = chart_df['Close'].rolling(window=5).mean()
                chart_df['ma20'] = chart_df['Close'].rolling(window=20).mean()
                chart_df['ma60'] = chart_df['Close'].rolling(window=60).mean()
                chart_df['ma120'] = chart_df['Close'].rolling(window=120).mean()
                
                # 시각화는 최근 100거래일만 슬라이싱
                chart_df = chart_df.iloc[-100:]
                
                fig = go.Figure()
                
                # 1) 일봉 캔들
                fig.add_trace(go.Candlestick(
                    x=chart_df.index,
                    open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'], close=chart_df['Close'],
                    name='일봉 캔들'
                ))
                
                # 2) 5일 이동평균선 (초록색)
                fig.add_trace(go.Scatter(
                    x=chart_df.index, y=chart_df['ma5'], 
                    line=dict(color='#2ca02c', width=1.5), 
                    name='5일 이평선'
                ))
                
                # 3) 20일 이동평균선 (빨간색 - 지지선 역할)
                fig.add_trace(go.Scatter(
                    x=chart_df.index, y=chart_df['ma20'], 
                    line=dict(color='#d62728', width=2.5), 
                    name='20일 이평선'
                ))
                
                # 4) 60일 이동평균선 (주황색)
                fig.add_trace(go.Scatter(
                    x=chart_df.index, y=chart_df['ma60'], 
                    line=dict(color='#ff7f0e', width=1.5), 
                    name='60일 이평선'
                ))

                # 5) 120일 이동평균선 (보라색)
                fig.add_trace(go.Scatter(
                    x=chart_df.index, y=chart_df['ma120'], 
                    line=dict(color='#9467bd', width=1.5), 
                    name='120일 이평선'
                ))
                
                # 6) 전고점 돌파 기준선 수평선
                fig.add_hline(
                    y=entry_price, line_dash="solid", line_color="green", line_width=2,
                    annotation_text=f"전고점 돌파 기준가 (${entry_price:,.2f})", 
                    annotation_position="top left",
                    annotation_font=dict(color="green", size=14, weight="bold")
                )

                fig.update_layout(
                    title=f"<b>{selected_stock_name} ({selected_code})</b> 일봉 이동평균선 & 돌파 차트",
                    yaxis=dict(
                        side="right",
                        tickformat="$.2f"  # 달러 가격 포맷으로 변경
                    ),
                    xaxis=dict(
                        rangeslider=dict(visible=False),
                        rangebreaks=[dict(bounds=["sat", "mon"])] # 주말 제거
                    ),
                    template='plotly_white',
                    height=550,
                    margin=dict(l=10, r=50, t=50, b=50),
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