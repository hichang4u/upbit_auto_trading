import pyupbit
import time
from datetime import datetime, timedelta
from utils.logger import log
from config.config import Config

class UpbitClient:
    def __init__(self):
        self.exchange = pyupbit.Upbit(Config.UPBIT_ACCESS_KEY, Config.UPBIT_SECRET_KEY)
        log.log('TR', "업비트 API 클라이언트 초기화 완료")
    
    def fetch_data(self, fetch_func, max_retries=20, delay=0.5):
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
    
    def get_ohlcv(self, market, interval='minute1', count=200):
        """OHLCV 데이터 조회"""
        try:
            # pyupbit의 get_ohlcv 메서드 사용
            df = pyupbit.get_ohlcv(ticker=market, 
                                  interval=interval, 
                                  count=count)
            
            if df is not None and not df.empty:
                return df
            else:
                log.log('WA', f"OHLCV 데이터가 비어있습니다: {market}")
                return None
                
        except Exception as e:
            log.log('WA', f"OHLCV 데이터 조회 실패: {str(e)}")
            return None
    
    def get_current_price(self, market):
        """현재가 조회"""
        try:
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
            if ticker is None:
                return self.exchange.get_balances()
            return self.exchange.get_balance(ticker)
        except Exception as e:
            log.log('WA', f"잔고 조회 중 오류: {str(e)}")
            return None
    
    def get_avg_buy_price(self, ticker):
        """평균 매수가 조회"""
        try:
            return self.exchange.get_avg_buy_price(ticker)
        except Exception as e:
            log.log('WA', f"평균 매수가 조회 중 오류: {str(e)}")
            return None
    
    def buy_market_order(self, market, price):
        """시장가 매수"""
        try:
            return self.exchange.buy_market_order(market, price)
        except Exception as e:
            log.log('WA', f"시장가 매수 중 오류: {str(e)}")
            return None
    
    def sell_market_order(self, market, volume):
        """시장가 매도"""
        try:
            return self.exchange.sell_market_order(market, volume)
        except Exception as e:
            log.log('WA', f"시장가 매도 중 오류: {str(e)}")
            return None
    
    def cancel_order(self, uuid):
        """주문 취소"""
        try:
            return self.exchange.cancel_order(uuid)
        except Exception as e:
            log.log('WA', f"주문 취소 중 오류: {str(e)}")
            return None
    
    def cancel_all_orders(self):
        """모든 미체결 주문 취소"""
        try:
            orders = self.exchange.get_order()
            if orders:
                for order in orders:
                    self.cancel_order(order['uuid'])
                log.log('TR', "모든 미체결 주문이 취소되었습니다.")
        except Exception as e:
            log.log('WA', f"미체결 주문 취소 중 오류: {str(e)}") 