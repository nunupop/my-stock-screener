import FinanceDataReader as fdr
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta, timezone

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

# 2. 전체 종목 검색 및 저장 (메인 실행 부)
def main():
    print("🚀 KOSPI 종목 데이터 수집을 시작합니다...")
    
    # 코스피 리스트 불러오기
    kospi_list = fdr.StockListing('KOSPI')
    
    # 검색 기간 (최근 150일 데이터면 계산에 충분함)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=150)
    
    results = []
    
    # 빠른 검색을 위해 병렬 처리(10개씩 동시에)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_stock, row, start_date, end_date): row for _, row in kospi_list.iterrows()}
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                results.append(res)
                print(f"✔️ 발견: {res['종목명']} ({res['종목코드']})")
                
    # 결과 저장하기
    if results:
        df = pd.DataFrame(results)
    else:
        # 검색된 종목이 없으면 빈 표(DataFrame) 생성
        df = pd.DataFrame(columns=['종목코드', '종목명', '진입가', '오늘종가'])
        
    df.to_csv('result.csv', index=False, encoding='utf-8-sig')
    
    # 3. 완벽한 한국 시간(KST)으로 마지막 업데이트 시간 저장
    KST = timezone(timedelta(hours=9))
    current_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    
    with open('last_update.txt', 'w', encoding='utf-8') as f:
        f.write(current_time)
        
    print(f"🎉 업데이트 완료! (완료시간: {current_time})")

# 프로그램 실행
if __name__ == "__main__":
    main()
