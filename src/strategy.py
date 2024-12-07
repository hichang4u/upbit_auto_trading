import pyupbit
import pandas as pd
import numpy as np
from utils.logger import log
from config.config import Config

class TradingStrategy:
    def __init__(self):
        self.position = None
        self.entry_price = None
        # 추가할 속성들
        self.trade_count = 0          # 거래 횟수
        self.win_count = 0            # 수익 거래 수
        self.loss_count = 0           # 손실 거래 수
        self.max_profit = 0           # 최대 수익률
        self.max_loss = 0             # 최대 손실률
        self.consecutive_losses = 0    # 연속 손실 횟수
        
    def calculate_indicators(self, market, period=20):
        """기존 지표에 추가할 지표들"""
        try:
            df = pyupbit.get_ohlcv(market, interval="day", count=period*2)
            
            # 1. 추세 지표
            df['EMA12'] = df['close'].ewm(span=12).mean()
            df['EMA26'] = df['close'].ewm(span=26).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal'] = df['MACD'].ewm(span=9).mean()
            
            # 2. 거래량 지표
            df['VMA20'] = df['volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['volume'] / df['VMA20']
            
            # 3. 변동성 지표
            df['ATR'] = self.calculate_atr(df)
            
            # 4. 모멘텀 지표
            df['ROC'] = df['close'].pct_change(periods=12) * 100
            
            return df.iloc[-1]
            
        except Exception as e:
            log.log('WA', f"지표 계산 중 오류: {str(e)}")
            return None
            
    def get_trading_signal(self, market):
        """매매 신호 생성"""
        try:
            # 1. 시장 상황 분석
            market_condition = self.analyze_market_condition()
            if market_condition == 'HIGH_RISK':
                return 'HOLD'
            
            # 2. 다중 시간대 분석
            daily_trend = self.analyze_trend("day")
            hourly_trend = self.analyze_trend("minute60")
            minute10_trend = self.analyze_trend("minute10")
            
            # 3. 지표 계산
            indicators = self.calculate_indicators(market)
            current_price = pyupbit.get_current_price(market)
            
            # 매수 신호 강화
            buy_signals = 0  # 매수 신호 카운트
            
            # 추세 확인
            if daily_trend in ['STRONG_UP', 'UP']: buy_signals += 2
            if hourly_trend in ['STRONG_UP', 'UP']: buy_signals += 2
            if minute10_trend in ['STRONG_UP']: buy_signals += 1
            
            # RSI 확인
            if indicators['RSI'] < 30: buy_signals += 2
            elif indicators['RSI'] < 40: buy_signals += 1
            
            # MACD 확인
            if indicators['MACD'] > indicators['Signal']: buy_signals += 1
            
            # 볼린저 밴드 확인
            if current_price < indicators['Lower'] * 1.02: buy_signals += 2
            
            # 거래량 확인
            if indicators['Volume_Ratio'] > 1.5: buy_signals += 1
            
            # 매수 조건
            if not self.position and buy_signals >= 6:  # 충분한 매수 신호
                if self.consecutive_losses < Config.MAX_CONSECUTIVE_LOSSES:
                    log.log('TR', f"매수 신호 강도: {buy_signals}/10")
                    return 'BUY'
            
            # 매도 신호 강화
            sell_signals = 0  # 매도 신호 카운트
            
            if self.position:
                # 수익률 기반 매도
                profit_rate = ((current_price - self.entry_price) / self.entry_price) * 100
                
                # 큰 수익 실현
                if profit_rate >= Config.PROFIT_RATE * 100:
                    log.log('TR', "목표 수익률 달성")
                    return 'SELL'
                
                # 손실 제한
                if profit_rate <= -Config.LOSS_RATE * 100:
                    log.log('TR', "손실 제한선 도달")
                    return 'SELL'
                
                # 추세 반전 확인
                if daily_trend in ['STRONG_DOWN', 'DOWN']: sell_signals += 2
                if hourly_trend in ['STRONG_DOWN', 'DOWN']: sell_signals += 2
                
                # RSI 확인
                if indicators['RSI'] > 70: sell_signals += 2
                
                # MACD 확인
                if indicators['MACD'] < indicators['Signal']: sell_signals += 1
                
                # 볼린저 밴드 확인
                if current_price > indicators['Upper'] * 0.98: sell_signals += 2
                
                # 매도 조건
                if sell_signals >= 5:
                    log.log('TR', f"매도 신호 강도: {sell_signals}/10")
                    return 'SELL'
            
            return 'HOLD'
            
        except Exception as e:
            log.log('WA', f"신호 생성 중 오류: {str(e)}")
            return 'HOLD'
    
    def analyze_market_condition(self):
        """시장 상황 분석"""
        try:
            # 1. 변동성 체크
            volatility = self.calculate_volatility()
            if volatility > Config.MAX_VOLATILITY:
                return 'HIGH_RISK'
            
            # 2. 거래량 체크
            volume_trend = self.analyze_volume_trend()
            if volume_trend == 'DECREASING':
                return 'LOW_VOLUME'
            
            # 3. 추세 강도 체크
            trend_strength = self.calculate_trend_strength()
            if trend_strength < Config.MIN_TREND_STRENGTH:
                return 'WEAK_TREND'
            
            return 'NORMAL'
            
        except Exception as e:
            log.log('WA', f"시장 분석 중 오류: {str(e)}")
            return 'HIGH_RISK'
    
    def update_trade_stats(self, profit_rate):
        """거래 통계 업데이트"""
        self.trade_count += 1
        if profit_rate > 0:
            self.win_count += 1
            self.consecutive_losses = 0
            self.max_profit = max(self.max_profit, profit_rate)
        else:
            self.loss_count += 1
            self.consecutive_losses += 1
            self.max_loss = min(self.max_loss, profit_rate)
    
    def calculate_volatility(self, period=20):
        """변동성 계산"""
        try:
            df = pyupbit.get_ohlcv(Config.MARKET, interval="day", count=period)
            if df is None:
                return float('inf')
            
            # True Range 계산
            df['H-L'] = df['high'] - df['low']
            df['H-PC'] = abs(df['high'] - df['close'].shift(1))
            df['L-PC'] = abs(df['low'] - df['close'].shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            
            # ATR (Average True Range) 계산
            df['ATR'] = df['TR'].rolling(window=period).mean()
            
            # 현재 변동성 (ATR / 현재가)
            current_volatility = df['ATR'].iloc[-1] / df['close'].iloc[-1]
            
            log.log('TR', f"현재 변동성: {current_volatility:.4f}")
            return current_volatility
            
        except Exception as e:
            log.log('WA', f"변동성 계산 중 오류: {str(e)}")
            return float('inf')
    
    def analyze_volume_trend(self, period=20):
        """거래량 추세 분석"""
        try:
            df = pyupbit.get_ohlcv(Config.MARKET, interval="day", count=period)
            if df is None:
                return 'DECREASING'
            
            # 거래량 이동평균
            df['VMA5'] = df['volume'].rolling(window=5).mean()
            df['VMA20'] = df['volume'].rolling(window=20).mean()
            
            # 거래량 추세 판단
            current_volume = df['volume'].iloc[-1]
            vma5 = df['VMA5'].iloc[-1]
            vma20 = df['VMA20'].iloc[-1]
            
            if current_volume > vma5 and vma5 > vma20:
                return 'INCREASING'
            elif current_volume < vma5 and vma5 < vma20:
                return 'DECREASING'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            log.log('WA', f"거래량 분석 중 오류: {str(e)}")
            return 'DECREASING'
    
    def calculate_trend_strength(self, period=20):
        """추세 강도 계산"""
        try:
            df = pyupbit.get_ohlcv(Config.MARKET, interval="day", count=period)
            if df is None:
                return 0
            
            # ADX (Average Directional Index) 계산
            df['TR'] = self.calculate_true_range(df)
            df['DM+'] = self.calculate_directional_movement(df, direction='plus')
            df['DM-'] = self.calculate_directional_movement(df, direction='minus')
            
            # Smoothed ATR
            df['ATR'] = df['TR'].rolling(window=period).mean()
            
            # Smoothed DM
            df['DM+_smooth'] = df['DM+'].rolling(window=period).mean()
            df['DM-_smooth'] = df['DM-'].rolling(window=period).mean()
            
            # Directional Indicators
            df['DI+'] = 100 * (df['DM+_smooth'] / df['ATR'])
            df['DI-'] = 100 * (df['DM-_smooth'] / df['ATR'])
            
            # ADX
            df['DX'] = 100 * abs(df['DI+'] - df['DI-']) / (df['DI+'] + df['DI-'])
            df['ADX'] = df['DX'].rolling(window=period).mean()
            
            trend_strength = df['ADX'].iloc[-1] / 100  # 0~1 사이 값으로 정규화
            
            log.log('TR', f"추세 강도: {trend_strength:.4f}")
            return trend_strength
            
        except Exception as e:
            log.log('WA', f"추세 강도 계산 중 오류: {str(e)}")
            return 0
    
    def calculate_true_range(self, df):
        """True Range 계산"""
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        ranges = [high - low, 
                 abs(high - close),
                 abs(low - close)]
        
        return pd.concat(ranges, axis=1).max(axis=1)
    
    def calculate_directional_movement(self, df, direction='plus'):
        """Directional Movement 계산"""
        high = df['high']
        low = df['low']
        
        if direction == 'plus':
            dm = high - high.shift(1)
            dm[dm < 0] = 0
            dm[(low.shift(1) - low) > (high - high.shift(1))] = 0
        else:
            dm = low.shift(1) - low
            dm[dm < 0] = 0
            dm[(high - high.shift(1)) > (low.shift(1) - low)] = 0
            
        return dm
    
    def analyze_trend(self, interval="day"):
        """다중 시간대 추세 분석"""
        try:
            df = pyupbit.get_ohlcv(Config.MARKET, interval=interval, count=40)
            if df is None:
                return 'UNKNOWN'
            
            # 1. 이동평균선 배열
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA10'] = df['close'].rolling(window=10).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            
            # 2. 이동평균선 정배열/역배열 확인
            last_idx = -1
            ma_trend = (df['MA5'].iloc[last_idx] > df['MA10'].iloc[last_idx] > df['MA20'].iloc[last_idx])
            ma_reverse = (df['MA5'].iloc[last_idx] < df['MA10'].iloc[last_idx] < df['MA20'].iloc[last_idx])
            
            # 3. 캔들 패턴 분석
            candle_pattern = self.analyze_candle_pattern(df.iloc[last_idx])
            
            # 4. 추세 판단
            if ma_trend and candle_pattern == 'BULLISH':
                return 'STRONG_UP'
            elif ma_trend:
                return 'UP'
            elif ma_reverse and candle_pattern == 'BEARISH':
                return 'STRONG_DOWN'
            elif ma_reverse:
                return 'DOWN'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            log.log('WA', f"추세 분석 중 오류: {str(e)}")
            return 'UNKNOWN'
    
    def analyze_candle_pattern(self, candle):
        """캔들 패턴 분석"""
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        
        # 양봉/음봉
        is_bullish = candle['close'] > candle['open']
        
        # 해머/역해머 패턴
        if lower_shadow > body * 2 and upper_shadow < body * 0.5:
            return 'BULLISH'  # 해머
        elif upper_shadow > body * 2 and lower_shadow < body * 0.5:
            return 'BEARISH'  # 역해머
            
        # 도지 패턴
        if body < (candle['high'] - candle['low']) * 0.1:
            return 'NEUTRAL'  # 도지
            
        return 'BULLISH' if is_bullish else 'BEARISH'