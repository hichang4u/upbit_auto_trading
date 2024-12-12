class BaseStrategy:
    def __init__(self):
        self.position = None
        self.entry_price = None
        self.client = None
        
    def set_client(self, client):
        """API 클라이언트 설정"""
        self.client = client
        
    def get_ohlcv(self, market):
        """기본 OHLCV 데이터 조회"""
        try:
            if self.client is None:
                raise Exception("API client not initialized")
            return self.client.get_ohlcv(market)
        except Exception as e:
            return None
    
    def get_current_price(self, market):
        """현재가 조회"""
        try:
            if self.client is None:
                raise Exception("API client not initialized")
            return self.client.get_current_price(market)
        except Exception as e:
            return None
    
    def calculate_indicators(self, market):
        """기본 지표 계산 (오버라이드 필요)"""
        raise NotImplementedError
    
    def get_trading_signal(self, market):
        """기본 매매 신호 생성 (오버라이드 필요)"""
        raise NotImplementedError
    
    def check_position(self, current_price):
        """포지션 상태 확인"""
        if self.position and self.entry_price:
            return (current_price - self.entry_price) / self.entry_price
        return None
    
    def enter_position(self, price):
        """포지션 진입"""
        self.position = True
        self.entry_price = price
    
    def exit_position(self):
        """포지션 청산"""
        self.position = False
        self.entry_price = None 