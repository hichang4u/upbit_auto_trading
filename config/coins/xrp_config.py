class XRPConfig:
    # XRP 기본 설정
    COIN_TICKER = 'XRP'
    MARKET = f'KRW-{COIN_TICKER}'
    
    # 매매 설정
    TRADE_UNIT = 10000
    PROFIT_RATE = 0.008
    LOSS_RATE = 0.008
    
    # XRP 특화 설정
    VOLATILITY_FACTOR = 0.5
    VOLUME_SURGE_THRESHOLD = 2.0
    BB_WIDTH = 1.8
    MIN_VOLUME_RATIO = 0.5
    
    # 기술적 지표 설정
    MA_PERIODS = [5, 10, 20, 60]
    BB_PERIOD = 20
    RSI_PERIOD = 14 