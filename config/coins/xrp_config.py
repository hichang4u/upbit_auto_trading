class XRPConfig:
    # XRP 기본 설정
    COIN_TICKER = 'XRP'
    MARKET = f'KRW-{COIN_TICKER}'
    
    # 매매 설정
    TRADE_UNIT = 10000  # 1만원 단위 매매
    PROFIT_RATE = 0.008      # 0.8% 익절
    LOSS_RATE = 0.006       # 0.6% 손절 (손실 제한을 더 타이트하게)
    
    # XRP 특화 설정
    VOLATILITY_FACTOR = 0.25  # 0.3 -> 0.25로 감소 (변동성 기준 강화)
    VOLUME_SURGE_THRESHOLD = 1.5  # 1.2 -> 1.5로 증가 (거래량 기준 강화)
    BB_WIDTH = 1.8
    MIN_VOLUME_RATIO = 0.6   # 0.5 -> 0.6으로 증가 (거래량 기준 강화)
    
    # 볼린저 밴드 설정
    BB_POSITION_BUY = 0.25    # 0.3 -> 0.25로 감소 (매수 기준 강화)
    BB_POSITION_SELL = 0.75   # 0.8 -> 0.75로 감소 (매도 기준 강화)
    MIN_PROFIT_FOR_VOLUME_SELL = 0.004  # 0.003 -> 0.004로 증가 (수익 기준 강화)
    
    # 기술적 지표 설정
    MA_PERIODS = [5, 10, 20, 60]
    BB_PERIOD = 20
    RSI_PERIOD = 14