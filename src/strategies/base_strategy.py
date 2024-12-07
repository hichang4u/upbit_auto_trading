class BaseStrategy:
    def __init__(self):
        self.position = None
        self.entry_price = None
        
    def get_ohlcv(self, market):
        """기본 OHLCV 데이터 조회"""
        pass
    
    def get_current_price(self, market):
        """현재가 조회"""
        pass
    
    def calculate_indicators(self, market):
        """기본 지표 계산 (오버라이드 필요)"""
        raise NotImplementedError
    
    def get_trading_signal(self, market):
        """기본 매매 신호 생성 (오버라이드 필요)"""
        raise NotImplementedError 