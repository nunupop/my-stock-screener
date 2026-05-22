import FinanceDataReader as fdr
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import warnings
import concurrent.futures

warnings.filterwarnings('ignore')

def process_stock(stock_info, start_date, end_date):
    code = stock_info['Symbol']
    name = stock_info['Name']
    
    if '.' in code or '$' in code: 
        return None
        
    try:
        df = fdr.DataReader(code, start_date, end_date)
        if len(df) < 40: return None
            
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
        
        df.dropna(inplace=True)
        if len(df) < 5: return None
        
        current = df.iloc[-1]
        
        is_bullish = current['Close'] > current['MA5'] > current['MA20']
        if not is_bullish: return None
            
        before_breakout_zone = df.iloc[-30:-5]
        resistance_level = before_breakout_zone['Close'].max()
        
        recent_3days = df.iloc[-3:]
        has_broken_out = (recent_3days['Close'] > resistance_level).any()
        if not has_broken_out: return None
            
        pullback_zone = df.iloc[-15:-3]
        if pullback_zone.empty: return None
        has_supported_20ma = ((pullback_zone['Low'] - pullback_zone['MA20']) / pullback_zone['MA20']).abs().min() < 0.02
        if not has_supported_20ma: return None
            
        is_volume_up = current['Volume'] > (current['Vol_MA20'] * 1.5)
        if not is_volume_up: return None
            
        return {
            '종목코드': code, 
            '종목명': name, 
            '진입가': round(float(resistance_level), 2),
            '오늘종가': round(float(current['Close']), 2)
        }
    except Exception:
        return None

def update_nasdaq_breakout_stocks_parallel():
    print("🇺🇸 나스닥 스크리닝 시작...")
    try:
        nasdaq_list = fdr.StockListing('NASDAQ')
    except Exception as e:
        print(f"로드 실패: {e}")
        return
        
    end_date = datetime.today()
    start_date = end_date - timedelta(days=300)
    stock_list = nasdaq_list[['Symbol', 'Name']].to_dict('records')
    result = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_stock, stock, start_date, end_date) for stock in stock_list]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                result.append(res)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 💡 나스닥 전용 파일명으로 분리 저장합니다.
    csv_path = os.path.join(current_dir, 'result_nasdaq.csv')
    txt_path = os.path.join(current_dir, 'last_update_nasdaq.txt')

    result_df = pd.DataFrame(result)
    if not result_df.empty:
        result_df = result_df.sort_values(by='종목코드', ascending=True)
    
    result_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    KST = timezone(timedelta(hours=9))
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"))
        
    print(f"💾 나스닥 저장 완료: {len(result_df)}개 종목")

if __name__ == "__main__":
    update_nasdaq_breakout_stocks_parallel()