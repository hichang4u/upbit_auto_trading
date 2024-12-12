import pyupbit
import time
from datetime import datetime, timedelta
from utils.logger import log
from config.config import Config

class UpbitClient:
    def __init__(self):
        self.exchange = pyupbit.Upbit(Config.UPBIT_ACCESS_KEY, Config.UPBIT_SECRET_KEY)
        self.market = Config.MARKET
        self.coin_ticker = Config.COIN_TICKER
        log.log('TR', "업비트 API 클라이언트 초기화 완료")
    
    def fetch_data(self, fetch_func, max_retries=20, delay=Config.MIN_API_INTERVAL):
        """API 호출 재시도 래퍼"""
        for i in range(max_retries):
            try:
                result = fetch_func()
                if result is not None:
                    return result
            except Exception as e:
                log.log('WA', f"API 호출 실패 ({i+1}/{max_retries}): {str(e)}")
            time.sleep(delay)
        return None
    
    def get_ohlcv(self, interval='minute1', count=200):
        """OHLCV 데이터 조회"""
        try:
            df = pyupbit.get_ohlcv(ticker=self.market, 
                                  interval=interval, 
                                  count=count)
            
            if df is not None and not df.empty:
                return df
            else:
                log.log('WA', f"OHLCV 데이터가 비어있습니다: {self.market}")
                return None
                
        except Exception as e:
            log.log('WA', f"OHLCV 데이터 조회 실패: {str(e)}")
            return None
    
    def get_current_price(self, market=None):
        """현재가 조회"""
        try:
            market = market or self.market
            price = pyupbit.get_current_price(market)
            if price is not None:
                return price
            log.log('WA', f"현재가 조회 실패: {market}")
            return None
        except Exception as e:
            log.log('WA', f"현재가 조회 중 오류: {str(e)}")
            return None
    
    def get_balance(self, ticker=None):
        """잔고 조회"""
        try:
            ticker = ticker or self.coin_ticker
            if ticker is None:
                return self.exchange.get_balances()
            return self.exchange.get_balance(ticker)
        except Exception as e:
            log.log('WA', f"잔고 조회 중 오류: {str(e)}")
            return None
    
    def get_avg_buy_price(self, ticker=None):
        """평균 매수가 조회"""
        try:
            ticker = ticker or self.coin_ticker
            return self.exchange.get_avg_buy_price(ticker)
        except Exception as e:
            log.log('WA', f"평균 매수가 조회 중 오류: {str(e)}")
            return None
    
    def buy_market_order(self, price, market=None):
        """시장가 매수"""
        try:
            market = market or self.market
            return self.exchange.buy_market_order(market, price)
        except Exception as e:
            log.log('WA', f"시장가 매수 중 오류: {str(e)}")
            return None
    
    def sell_market_order(self, volume, market=None):
        """시장가 매도"""
        try:
            market = market or self.market
            return self.exchange.sell_market_order(market, volume)
        except Exception as e:
            log.log('WA', f"시장가 매도 중 오류: {str(e)}")
            return None
    
    def get_orders(self, market=None, state="wait"):
        """미체결 주문 조회"""
        try:
            market = market or self.market
            return self.exchange.get_order(market, state=state)
        except Exception as e:
            log.log('WA', f"미체결 주문 조회 중 오류: {str(e)}")
            return []
    
    def cancel_order(self, uuid):
        """주문 취소"""
        try:
            return self.exchange.cancel_order(uuid)
        except Exception as e:
            log.log('WA', f"주문 취소 중 오류: {str(e)}")
            return None
    
    def cancel_orders(self, market=None):
        """특정 마켓의 미체결 주문 취소"""
        try:
            market = market or self.market
            orders = self.get_orders(market)
            if orders:
                for order in orders:
                    self.cancel_order(order['uuid'])
            elif isinstance(orders, dict):
                self.cancel_order(orders['uuid'])
        except Exception as e:
            log.log('WA', f"미체결 주문 취소 중 오류: {str(e)}")
    
    def cancel_all_orders(self):
        """모든 미체결 주문 취소"""
        try:
            orders = self.get_orders(self.market)
            if orders:
                if isinstance(orders, list):
                    for order in orders:
                        self.cancel_order(order['uuid'])
                elif isinstance(orders, dict):
                    self.cancel_order(orders['uuid'])
        except Exception as e:
            log.log('WA', f"전체 미체결 주문 취소 중 오류: {str(e)}") 