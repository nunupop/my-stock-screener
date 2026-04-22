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
