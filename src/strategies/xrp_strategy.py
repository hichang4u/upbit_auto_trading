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
                
                ma_trend = self.check_ma_trend(indicators)
                
                # 매수 조건 로깅 (간단히)
                if volatility_signal and bb_position < self.config.BB_POSITION_BUY:
                    log.system_log('INFO', f"=== 매수 조건 충족 여부 ===")
                    log.system_log('INFO', f"현재가/목표가: {current_price:,.0f}/{indicators['TARGET']:,.0f}")
                    log.system_log('INFO', f"거래량/BB/MA: {volume_surge}/{bb_position < self.config.BB_POSITION_BUY}/{ma_trend}")
                
                if (volatility_signal and 
                    bb_position < self.config.BB_POSITION_BUY and 
                    (volume_surge or ma_trend)):
                    self.enter_position(current_price)
                    return 'BUY'
            
            # 매도 신호
            else:
                profit_rate = self.check_position(current_price)
                bb_position = (current_price - indicators['BB_LOWER']) / \
                             (indicators['BB_UPPER'] - indicators['BB_LOWER'])
                
                # 매도 조건 로깅 (수익이 있을 때만)
                if profit_rate > 0:
                    log.system_log('INFO', f"=== 매도 조건 검토 ===")
                    log.system_log('INFO', f"수익률: {profit_rate:.2f}%")
                    if bb_position > self.config.BB_POSITION_SELL:
                        log.system_log('INFO', "BB 상단 도달")
                    if indicators['VOL_RATIO'] < self.config.MIN_VOLUME_RATIO:
                        log.system_log('INFO', "거래량 감소")
                
                # 익절/손절
                if profit_rate >= self.config.PROFIT_RATE or profit_rate <= -self.config.LOSS_RATE:
                    self.exit_position()
                    return 'SELL'
                
                # 추가 매도 조건
                if (bb_position > self.config.BB_POSITION_SELL or 
                    (indicators['VOL_RATIO'] < self.config.MIN_VOLUME_RATIO and profit_rate > self.config.MIN_PROFIT_FOR_VOLUME_SELL)):
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