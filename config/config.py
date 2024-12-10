import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
    UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')
    
    # 거래 설정
    SIMULATION_MODE = False    # 시뮬레이션 모드 여부
    COIN_TICKER = 'XRP'      # 거래할 코인(XRP, BTC, ETH, SOL, DOGE, ADA)
    CURRENCY = 'KRW'         # 거래 통화
    MARKET = f'{CURRENCY}-{COIN_TICKER}'
    
    # 매매 설정
    TRADE_UNIT = 10000       # 매매 단위 (1만원)
    PROFIT_RATE = 0.008      # 목표 수익률 (0.8%)
    LOSS_RATE = 0.008        # 손실 제한 (-0.8%)
    TRADE_INTERVAL = 10      # 거래 간격 10초
    SELL_ALL_ON_STOP = False # 종료 시 전량 매도 여부
    
    # 출력 형식 설정
    PRICE_DECIMAL = 2        # 가격 소수점 자릿수
    VOLUME_DECIMAL = 4       # 수량 소수점 자릿수
    PROFIT_DECIMAL = 2       # 수익률 소수점 자릿수
    
    # 시뮬레이션 설정
    SIMULATION_CASH = 100000  # 시뮬레이션 시작 금액 (10만원)
    SIMULATION_COIN = 0        # 시뮬레이션 시작 코인 수량
    
    # 전략 설정
    MAX_VOLATILITY = 0.05     # 최대 허용 변동성
    MIN_TREND_STRENGTH = 0.6  # 최소 추세 강도
    MAX_TRADE_COUNT = 5       # 일일 최대 거래 횟수
    MAX_CONSECUTIVE_LOSSES = 3 # 최대 연속 손실 횟수
    BUY_SIGNAL_THRESHOLD = 6  # 매수 신호 임계값
    SELL_SIGNAL_THRESHOLD = 5 # 매도 신호 임계값
    
    # 분석 설정
    ENABLE_ANALYSIS = True           # 자동 분석 활성화
    ANALYSIS_TIME = "23:50"          # 일일 분석 시간
    ANALYSIS_DAYS = 30               # 분석 기간 (일)
    AUTO_ADJUST_PARAMS = True        # 파라미터 자동 조정
    
    # 거래 시간 설정(코인은 24시간 거래 가능)
    #TRADING_START_HOUR = 9           # 거래 시작 시간
    #TRADING_END_HOUR = 23            # 거래 종료 시간
    
    # 거래 간격 설정
    MIN_TRADE_INTERVAL = 5   # 최소 허용 간격
    MAX_TRADE_INTERVAL = 60  # 최대 허용 간격
    AUTO_ADJUST_INTERVAL = True  # 거래 간격 자동 조정 여부
    
    # API 설정
    MAX_API_CALLS = 600      # 분당 최대 API 호출 수
    MIN_API_INTERVAL = 0.1   # API 호출 간 최소 간격 (초)