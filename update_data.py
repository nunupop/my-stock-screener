import FinanceDataReader as fdr
import pandas as pd
import os
from datetime import datetime, timedelta
import warnings
import concurrent.futures

warnings.filterwarnings('ignore')

# 1. 개별 종목을 처리하는 함수 (병렬 작업을 위해 분리)
def process_stock(stock_info, start_date, end_date):
    code = stock_info['Code']
    name = stock_info['Name']
    
    try:
        # 데이터 수집
        df = fdr.DataReader(code, start_date, end_date)
        if len(df) < 120: return None
            
        # 파인스크립트 방식 볼린저 밴드 계산 (ddof=0 적용)
        df['ma20'] = df['Close'].rolling(window=20).mean()
        df['std20'] = df['Close'].rolling(window=20).std(ddof=0)
        df['upper'] = df['ma20'] + 2 * df['std20']
        df['lower'] = df['ma20'] - 2 * df['std20']
        df['bb_width'] = df['upper'] - df['lower']
        
        df = df.dropna()
        
        # 룩백 100봉 기준 압축 시점 탐색
        recent_100 = df.tail(100)
        if len(recent_100) < 100: return None
            
        min_width_idx = recent_100['bb_width'].idxmin()
        after_squeeze = df.loc[min_width_idx:]
        
        if len(after_squeeze) < 1: return None
            
        # 돌파 로직: '고가(High)' 기준
        today_high = after_squeeze.iloc[-1]['High']
        today_upper = after_squeeze.iloc[-1]['upper']
        today_close = after_squeeze.iloc[-1]['Close']
        
        # 고가가 상단을 돌파했는지 확인
        if today_high > today_upper:
            if len(after_squeeze) > 1:
                past_data = after_squeeze.iloc[:-1]
                # 과거 고가가 상단을 뚫은 적이 한 번도 없는지 검사
                if not (past_data['High'] > past_data['upper']).any():
                    return {'종목코드': code, '종목명': name, '현재가': today_close, '오늘고가': today_high}
            else:
                return {'종목코드': code, '종목명': name, '현재가': today_close, '오늘고가': today_high}
    except Exception:
        # 상장폐지, 거래정지 등 데이터 수집 에러 발생 시 무시
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