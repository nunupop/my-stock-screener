import streamlit as st
import pandas as pd
import os
import base64
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 1. 페이지 기본 설정
st.set_page_config(page_title="나스닥 돌파 검색", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'bg.jpg')

# CSS (배경 + 공통 스타일)
bg_style = ""
if os.path.exists(image_path):
    img_base64 = get_base64_of_bin_file(image_path)
    bg_style = f"""
    .stApp {{
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    """

st.markdown(
    f"""
    <style>
    {bg_style}

    /* 공통 알림창 글씨 */
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

    /* ───── HTML 직접 렌더 테이블 스타일 ───── */
    .custom-table {{
        width: 100%;
        border-collapse: collapse;
        background-color: #000000;
        border: 2px solid #FFFFFF;
        border-radius: 8px;
        overflow: hidden;
        font-size: 15px;
    }}
    .custom-table thead tr {{
        background-color: #282828;
    }}
    .custom-table th {{
        color: #FFFFFF;
        font-weight: bold;
        padding: 10px 14px;
        border: 1px solid #FFFFFF;
        text-align: center;
    }}
    .custom-table td {{
        color: #FFFFFF;
        background-color: #0f0f0f;
        padding: 9px 14px;
        border: 1px solid #FFFFFF;
        text-align: center;
    }}
    .custom-table tr:hover td {{
        background-color: #1e1e1e;
    }}
    .custom-table a {{
        color: #90CAF9;
        text-decoration: none;
        font-weight: 500;
    }}
    .custom-table a:hover {{
        text-decoration: underline;
        color: #BBDEFB;
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
        <div style='text-align: right; font-size: 12px; color: #E0E0E0; font-style: italic; margin-top: 10px;'>
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

# 데이터 로드 및 HTML 테이블 렌더링
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    if not df.empty:
        st.success(f"🎉 총 {len(df)}개의 나스닥 종목이 검색되었습니다!")

        # 티커 대문자 변환
        df['종목코드'] = df['종목코드'].astype(str).str.upper()

        # HTML 테이블 직접 생성
        rows_html = ""
        for _, row in df.iterrows():
            ticker = row['종목코드']
            name   = row['종목명']
            entry  = float(row['진입가'])
            close  = float(row['오늘종가'])
            url    = f"https://finance.yahoo.com/quote/{ticker}"
            rows_html += f"""
            <tr>
                <td>{ticker}</td>
                <td>{name}</td>
                <td>${entry:,.2f}</td>
                <td>${close:,.2f}</td>
                <td><a href="{url}" target="_blank">Yahoo Finance 📈</a></td>
            </tr>
            """

        table_html = f"""
        <table class="custom-table">
            <thead>
                <tr>
                    <th>티커</th>
                    <th>기업명</th>
                    <th>돌파 기준가($)</th>
                    <th>오늘 종가($)</th>
                    <th>차트 바로가기</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        st.markdown("---")

        # 차트 시각화
        st.markdown("<h3 style='color: white; text-shadow: 1px 1px 2px black;'>📊 화면에서 바로 차트 확인하기</h3>", unsafe_allow_html=True)

        stock_list = df['종목명'].tolist()
        selected_stock_name = st.selectbox("종목을 선택하세요:", stock_list)

        if selected_stock_name:
            selected_code = df[df['종목명'] == selected_stock_name]['종목코드'].values[0]
            entry_price   = df[df['종목명'] == selected_stock_name]['진입가'].values[0]

            start_date = datetime.now() - timedelta(days=300)
            start_str  = start_date.strftime('%Y-%m-%d')

            chart_df = yf.download(selected_code, start=start_str, progress=False)

            if not chart_df.empty:
                if isinstance(chart_df.columns, pd.MultiIndex):
                    chart_df.columns = chart_df.columns.droplevel(1)

                chart_df['ma5']   = chart_df['Close'].rolling(window=5).mean()
                chart_df['ma20']  = chart_df['Close'].rolling(window=20).mean()
                chart_df['ma60']  = chart_df['Close'].rolling(window=60).mean()
                chart_df['ma120'] = chart_df['Close'].rolling(window=120).mean()

                chart_df = chart_df.iloc[-100:]

                fig = go.Figure()

                fig.add_trace(go.Candlestick(
                    x=chart_df.index,
                    open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'],   close=chart_df['Close'],
                    name='일봉 캔들'
                ))

                fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['ma5'],   line=dict(color='#2ca02c', width=1.5), name='5일선'))
                fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['ma20'],  line=dict(color='#d62728', width=2.5), name='20일선'))
                fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['ma60'],  line=dict(color='#ff7f0e', width=1.5), name='60일선'))
                fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['ma120'], line=dict(color='#9467bd', width=1.5), name='120일선'))

                fig.add_hline(
                    y=entry_price, line_dash="solid", line_color="green", line_width=2,
                    annotation_text=f"전고점 기준가 (${entry_price:,.2f})",
                    annotation_position="top left",
                    annotation_font=dict(color="green", size=14, weight="bold")
                )

                fig.update_layout(
                    title=f"<b>{selected_stock_name} ({selected_code})</b> 일봉 차트",
                    yaxis=dict(side="right", tickformat="$.2f"),
                    xaxis=dict(rangeslider=dict(visible=False), rangebreaks=[dict(bounds=["sat", "mon"])]),
                    template='plotly_white',
                    height=550,
                    margin=dict(l=10, r=50, t=50, b=50),
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("해당 종목의 차트 데이터를 불러올 수 없습니다.")

    else:
        st.warning("오늘은 조건에 부합하는 종목이 없습니다.")
else:
    st.info("데이터를 수집하는 중입니다. 잠시 후 다시 확인해주세요.")
