from src.strategies.base_strategy import BaseStrategy
from config.coins.xrp_config import XRPConfig
from config.config import Config
from utils.logger import log
from datetime import datetime

class XRPStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.config = XRPConfig
        self.balance = 0  # 보유 현금
        self.coin_balance = 0  # 보유 코인
        self.position = False  # 포지션 상태
        self.position_price = 0  # 진입 가격
        
    def get_balance(self):
        """현재 보유 현금 조회"""
        return self.balance
        
    def get_coin_balance(self):
        """현재 보유 코인 수량 조회"""
        return self.coin_balance
        
    def enter_position(self, price):
        """매수 포지션 진입"""
        self.position = True
        self.position_price = price
        
    def exit_position(self):
        """매도 포지션 청산"""
        self.position = False
        self.position_price = 0
        
    def check_position(self, current_price):
        """포지션 수익률 계산"""
        if not self.position or self.position_price == 0:
            return 0
        return ((current_price - self.position_price) / self.position_price) * 100
    
    def calculate_rsi(self, df, period=14):
        """RSI 계산 함수"""
        try:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            log.log('WA', f"RSI 계산 중 오류: {str(e)}")
            return None
    
    def calculate_indicators(self, market):
        """XRP 특화 지표"""
        try:
            df = self.get_ohlcv(market)
            if df is None or df.empty:
                return None
            
            # XRP 특화 지표 계산
            df['RANGE'] = df['high'] - df['low']
            df['TARGET'] = df['open'] + df['RANGE'].shift(1) * self.config.VOLATILITY_FACTOR
            
            # 거래량 분석 (5일 이동평균 및 전일 대비 증감)
            df['VOL_MA5'] = df['volume'].rolling(window=5).mean()
            df['VOL_RATIO'] = df['volume'] / df['VOL_MA5']
            df['VOL_CHANGE'] = df['volume'].pct_change()  # 전일 대비 거래량 변화율
            
            # 이동평균선
            for period in self.config.MA_PERIODS:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            
            # 볼린저 밴드
            df['BB_MID'] = df['close'].rolling(window=self.config.BB_PERIOD).mean()
            df['BB_STD'] = df['close'].rolling(window=self.config.BB_PERIOD).std()
            df['BB_UPPER'] = df['BB_MID'] + df['BB_STD'] * self.config.BB_WIDTH
            df['BB_LOWER'] = df['BB_MID'] - df['BB_STD'] * self.config.BB_WIDTH
            
            # RSI 지표 계산 추가
            df['RSI'] = self.calculate_rsi(df)
            
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
                # RSI 조건
                rsi_buy_condition = indicators['RSI'] <= 25
                
                # 볼린저 밴드 하단 조건
                bb_lower_condition = current_price <= indicators['BB_LOWER']
                
                # 거래량 증가 조건
                volume_increase_condition = indicators['VOL_CHANGE'] > 0
                
                # 매수 조건 로깅
                log.system_log('INFO', f"=== 매수 조건 검토 ===")
                log.system_log('INFO', f"RSI: {indicators['RSI']:.2f} (기준: 25 이하) - {rsi_buy_condition}")
                log.system_log('INFO', f"볼린저 밴드 하단: {indicators['BB_LOWER']:.2f} (현재가: {current_price:.2f}) - {bb_lower_condition}")
                log.system_log('INFO', f"거래량 증가 여부: {volume_increase_condition} (변화율: {indicators['VOL_CHANGE']*100:.2f}%)")
                
                # 모든 조건 충족 시 매수
                if rsi_buy_condition and bb_lower_condition and volume_increase_condition:
                    log.system_log('INFO', "✅ 모든 매수 조건 충족!")
                    self.enter_position(current_price)
                    return 'BUY'
            
            # 매도 신호
            else:
                profit_rate = self.check_position(current_price)
                
                # RSI 조건
                rsi_sell_condition = indicators['RSI'] >= 75
                
                # 볼린저 밴드 상단 조건
                bb_upper_condition = current_price >= indicators['BB_UPPER']
                
                # 거래량 증가 조건
                volume_increase_condition = indicators['VOL_CHANGE'] > 0
                
                # 매도 조건 로깅
                log.system_log('INFO', f"=== 매도 조건 검토 ===")
                log.system_log('INFO', f"수익률: {profit_rate:.2f}%")
                log.system_log('INFO', f"RSI: {indicators['RSI']:.2f} (기준: 75 이상) - {rsi_sell_condition}")
                log.system_log('INFO', f"볼린저 밴드 상단: {indicators['BB_UPPER']:.2f} (현재가: {current_price:.2f}) - {bb_upper_condition}")
                log.system_log('INFO', f"거래량 증가 여부: {volume_increase_condition} (변화율: {indicators['VOL_CHANGE']*100:.2f}%)")
                
                # 익절/손절 (기존 조건 유지)
                if profit_rate >= self.config.PROFIT_RATE or profit_rate <= -self.config.LOSS_RATE:
                    log.system_log('INFO', f"익절/손절 조건 충족 (수익률: {profit_rate:.2f}%)")
                    self.exit_position()
                    return 'SELL'
                
                # 모든 조건 충족 시 매도
                if rsi_sell_condition and bb_upper_condition and volume_increase_condition:
                    log.system_log('INFO', "✅ 모든 매도 조건 충족!")
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
            # 이동평균선 값 로깅 (간단히)
            if all(ma_values[i] >= ma_values[i+1] for i in range(len(ma_values)-1)):
                log.system_log('INFO', "이동평균선 정배열 확인")
            return all(ma_values[i] >= ma_values[i+1] for i in range(len(ma_values)-1))
        except Exception as e:
            log.log('WA', f"이동평균선 정배열 확인 중 오류: {str(e)}")
            return False