class BTCConfig:
    # BTC 기본 설정
    COIN_TICKER = 'BTC'
    MARKET = f'KRW-{COIN_TICKER}'
    
    # 매매 설정
    TRADE_UNIT = 20000
    PROFIT_RATE = 0.01
    LOSS_RATE = 0.01
    
    # BTC 특화 설정
    VOLATILITY_FACTOR = 0.4
    VOLUME_SURGE_THRESHOLD = 1.5
    BB_WIDTH = 2.0
    MIN_VOLUME_RATIO = 0.7 