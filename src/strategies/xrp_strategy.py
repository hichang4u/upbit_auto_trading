from src.strategies.base_strategy import BaseStrategy
from config.coins.xrp_config import XRPConfig
from utils.logger import log

class XRPStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.config = XRPConfig
    
    def calculate_indicators(self, market):
        """XRP 특화 지표"""
        try:
            df = self.get_ohlcv(market)
            if df is None or df.empty:
                return None
            
            # XRP 특화 지표 계산
            df['RANGE'] = df['high'] - df['low']
            df['TARGET'] = df['open'] + df['RANGE'].shift(1) * self.config.VOLATILITY_FACTOR
            
            # 거래량 분석
            df['VOL_MA5'] = df['volume'].rolling(window=5).mean()
            df['VOL_RATIO'] = df['volume'] / df['VOL_MA5']
            
            # 이동평균선
            for period in self.config.MA_PERIODS:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            
            # 볼린저 밴드
            df['BB_MID'] = df['close'].rolling(window=self.config.BB_PERIOD).mean()
            df['BB_STD'] = df['close'].rolling(window=self.config.BB_PERIOD).std()
            df['BB_UPPER'] = df['BB_MID'] + df['BB_STD'] * self.config.BB_WIDTH
            df['BB_LOWER'] = df['BB_MID'] - df['BB_STD'] * self.config.BB_WIDTH
            
            return df.iloc[-1]
            
        except Exception as e:
            log.log('WA', f"지표 계산 중 오류: {str(e)}")
            return None
    
    def get_trading_signal(self, market):
        """매매 신호 생성"""
        try:
            current_price = self.get_current_price(market)
            if current_price is None:
                return 'HOLD'
            
            indicators = self.calculate_indicators(market)
            if indicators is None:
                return 'HOLD'
            
            # 매수 신호
            if not self.position:
                volatility_signal = current_price > indicators['TARGET']
                volume_surge = indicators['VOL_RATIO'] > self.config.VOLUME_SURGE_THRESHOLD
                
                bb_position = (current_price - indicators['BB_LOWER']) / \
                             (indicators['BB_UPPER'] - indicators['BB_LOWER'])
                
                if (volatility_signal and 
                    bb_position < 0.3 and 
                    (volume_surge or self.check_ma_trend(indicators))):
                    self.enter_position(current_price)
                    return 'BUY'
            
            # 매도 신호
            else:
                profit_rate = self.check_position(current_price)
                
                # 익절/손절
                if profit_rate >= self.config.PROFIT_RATE or profit_rate <= -self.config.LOSS_RATE:
                    self.exit_position()
                    return 'SELL'
                
                # 추가 매도 조건
                bb_position = (current_price - indicators['BB_LOWER']) / \
                             (indicators['BB_UPPER'] - indicators['BB_LOWER'])
                
                if (bb_position > 0.8 or 
                    (indicators['VOL_RATIO'] < self.config.MIN_VOLUME_RATIO and profit_rate > 0.003)):
                    self.exit_position()
                    return 'SELL'
            
            return 'HOLD'
            
        except Exception as e:
            log.log('WA', f"매매 신호 생성 중 오류: {str(e)}")
            return 'HOLD'
    
    def check_ma_trend(self, indicators):
        """이동평균선 정배열 확인"""
        try:
            ma_values = [indicators[f'MA{period}'] for period in sorted(self.config.MA_PERIODS)]
            return all(ma_values[i] >= ma_values[i+1] for i in range(len(ma_values)-1))
        except Exception as e:
            log.log('WA', f"이동평균선 정배열 확인 중 오류: {str(e)}")
            return False