
import FinanceDataReader as fdr
import pandas as pd
import os
from datetime import datetime, timedelta
import warnings
import concurrent.futures

warnings.filterwarnings('ignore')

# 1. 개별 종목을 처리하는 함수 (종가 마감 확인 로직 적용)
def process_stock(stock_info, start_date, end_date):
    code = stock_info['Code']
    name = stock_info['Name']
    
    try:
        df = fdr.DataReader(code, start_date, end_date)
        if len(df) < 120: return None
            
        # 볼린저 밴드 계산 (ddof=0)
        df['ma20'] = df['Close'].rolling(window=20).mean()
        df['std20'] = df['Close'].rolling(window=20).std(ddof=0)
        df['upper'] = df['ma20'] + 2 * df['std20']
        df['lower'] = df['ma20'] - 2 * df['std20']
        df['bb_width'] = df['upper'] - df['lower']
        
        # 1. 100일 압축 확인
        df['min_w1'] = df['bb_width'].rolling(window=100).min()
        df['is_min1'] = df['bb_width'] == df['min_w1']
        
        df = df.dropna()
        if len(df) < 1: return None
        
        # 2. 가장 최근 압축일 찾기 (오늘은 제외)
        past_df = df.iloc[:-1]
        squeeze_days = past_df[past_df['is_min1']]
        if squeeze_days.empty: return None
        
        last_squeeze_idx = squeeze_days.index[-1]
        
        # 3. 압축일 이후 '처음으로' 고가가 상단을 뚫은 날(기준봉) 찾기
        after_squeeze = df.loc[last_squeeze_idx:]
        breakout_candidates = after_squeeze[after_squeeze['High'] > after_squeeze['upper']]
        
        if breakout_candidates.empty: return None # 상단을 찌른 적조차 없으면 탈락
        
        first_breakout_idx = breakout_candidates.index[0]
        reference_high = df.loc[first_breakout_idx, 'High'] # 기준봉의 고가 기억!
        
        # 4. 종가 마감 확인: 기준봉 이후의 데이터에서 종가가 기준봉의 고가를 돌파한 날 찾기
        after_breakout = df.loc[first_breakout_idx:]
        confirmed_days = after_breakout[after_breakout['Close'] > reference_high]
        
        if confirmed_days.empty:
            return None # 윗꼬리만 달고 아직 종가로 뚫어낸 적이 없다면 탈락
            
        # 5. 종가로 뚫어낸 첫 번째 날이 바로 '오늘'인지 확인
        first_confirmed_idx = confirmed_days.index[0]
        
        if first_confirmed_idx == df.index[-1]:
            today_close = df['Close'].iloc[-1]
            return {
                '종목코드': code, 
                '종목명': name, 
                '돌파기준가(기준봉고가)': reference_high,
                '오늘종가': today_close
            }
            
    except Exception:
        return None
        
    return None


def update_tv_pinescript_breakout_stocks_parallel():
    print("데이터 수집 및 종목 검색 시작 (병렬 처리 적용)...")
    
    # KRX 전체 수집 후 코스피 보통주 필터링
    krx_list = fdr.StockListing('KRX')
    kospi_list = krx_list[krx_list['Market'] == 'KOSPI']
    kospi_list = kospi_list[kospi_list['Code'].str.endswith('0')]
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=300)
    
    # 병렬 처리를 위해 종목 정보를 딕셔너리 리스트로 변환
    stock_list = kospi_list[['Code', 'Name']].to_dict('records')
    result = []
    
    print(f"총 {len(stock_list)}개 종목을 10개씩 동시에 검색합니다. 잠시만 기다려주세요...")
    
    # 2. ThreadPoolExecutor를 이용한 병렬 처리 (작업자 10명 투입)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # 각 종목별로 작업을 할당
        futures = [executor.submit(process_stock, stock, start_date, end_date) for stock in stock_list]
        
        # 작업이 완료되는 대로 결과를 수집
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                result.append(res)

    # 현재 실행 중인 파이썬 파일의 진짜 폴더 위치 알아내기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 그 폴더 위치에 파일 이름 합치기
    csv_path = os.path.join(current_dir, 'result.csv')
    txt_path = os.path.join(current_dir, 'last_update.txt')

    # 3. 검색 결과를 CSV 파일로 명시적 저장
    result_df = pd.DataFrame(result)
    result_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # 4. 마지막 업데이트 시간 저장
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    print(f"업데이트 완료! 총 {len(result_df)}개 종목 저장됨.")

# --- 빠져있던 실행 명령 추가 ---
if __name__ == "__main__":
    update_tv_pinescript_breakout_stocks_parallel()
