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
            # 입력값 검증
            if ticker is not None and not isinstance(ticker, str):
                log.log('WA', f"잘못된 ticker 형식: {ticker} (타입: {type(ticker).__name__})")
                return 0
                
            ticker = ticker or self.coin_ticker
            
            if ticker is None:
                log.log('WA', "ticker가 None이고 self.coin_ticker도 None입니다")
                return 0
                
            # 전체 잔고 조회 요청
            if ticker.lower() == 'all':
                try:
                    balances = self.exchange.get_balances()
                    if balances is None:
                        log.log('WA', "전체 잔고 조회 결과가 None입니다")
                        return {}
                    return balances
                except Exception as e:
                    if hasattr(log, 'detailed_error'):
                        log.detailed_error("전체 잔고 조회 중 오류", e)
                    else:
                        log.log('WA', f"전체 잔고 조회 중 오류: {str(e)}")
                    return {}
            
            # 특정 코인 잔고 조회
            try:
                balance = self.exchange.get_balance(ticker)
                # 결과 검증
                if balance is None:
                    log.log('TR', f"{ticker} 잔고가 없습니다")
                    return 0
                
                # 문자열인 경우 float로 변환
                if isinstance(balance, str):
                    try:
                        balance = float(balance)
                    except (ValueError, TypeError):
                        log.log('WA', f"{ticker} 잔고 문자열 변환 실패: {balance}")
                        return 0
                
                return balance
                
            except Exception as e:
                if hasattr(log, 'detailed_error'):
                    log.detailed_error(f"{ticker} 잔고 조회 중 오류", e)
                else:
                    log.log('WA', f"{ticker} 잔고 조회 중 오류: {str(e)}")
                return 0
                
        except Exception as e:
            if hasattr(log, 'detailed_error'):
                log.detailed_error("잔고 조회 함수 실행 중 예상치 못한 오류", e)
            else:
                log.log('WA', f"잔고 조회 중 예상치 못한 오류: {str(e)}")
            return 0
    
    def get_avg_buy_price(self, ticker=None):
        """평균 매수가 조회"""
        try:
            # 입력값 검증
            if ticker is not None and not isinstance(ticker, str):
                log.log('WA', f"잘못된 ticker 형식: {ticker} (타입: {type(ticker).__name__})")
                return 0
                
            ticker = ticker or self.coin_ticker
            
            if ticker is None:
                log.log('WA', "ticker가 None이고 self.coin_ticker도 None입니다")
                return 0
            
            # 평균 매수가 조회
            try:
                avg_price = self.exchange.get_avg_buy_price(ticker)
                
                # 결과 검증
                if avg_price is None:
                    log.log('TR', f"{ticker} 평균 매수가가 없습니다")
                    return 0
                
                # 문자열인 경우 float로 변환
                if isinstance(avg_price, str):
                    try:
                        avg_price = float(avg_price)
                    except (ValueError, TypeError):
                        log.log('WA', f"{ticker} 평균 매수가 문자열 변환 실패: {avg_price}")
                        return 0
                
                return avg_price
                
            except Exception as e:
                if hasattr(log, 'detailed_error'):
                    log.detailed_error(f"{ticker} 평균 매수가 조회 중 오류", e)
                else:
                    log.log('WA', f"{ticker} 평균 매수가 조회 중 오류: {str(e)}")
                return 0
                
        except Exception as e:
            if hasattr(log, 'detailed_error'):
                log.detailed_error("평균 매수가 조회 함수 실행 중 예상치 못한 오류", e)
            else:
                log.log('WA', f"평균 매수가 조회 중 예상치 못한 오류: {str(e)}")
            return 0
    
    def buy_market_order(self, market=None, price=None):
        """시장가 매수"""
        try:
            market = market or self.market
            
            # market과 price 순서가 바뀐 경우 처리
            if isinstance(market, (int, float)) and isinstance(price, str):
                log.log('WA', f"매개변수 순서가 바뀐 것으로 보입니다. 자동 교정: market={price}, price={market}")
                market, price = price, market
            
            # 타입 확인 및 변환
            if price is None:
                error_msg = "매수 금액(price)이 지정되지 않았습니다."
                log.log('WA', error_msg)
                raise ValueError(error_msg)
            
            # 숫자 타입으로 변환
            if isinstance(price, str):
                try:
                    price = float(price)
                except ValueError as e:
                    error_msg = f"유효하지 않은 가격 형식: {price}"
                    log.log('WA', error_msg)
                    raise ValueError(error_msg) from e
            
            log.log('TR', f"시장가 매수 시도: {market}, {price:,.0f}원")
            
            # 매개변수 출력 (디버깅용)
            log.log('TR', f"매수 API 호출 매개변수: market={market}, price={price}, 타입: market={type(market).__name__}, price={type(price).__name__}")
            
            # 실제 API 호출
            result = self.exchange.buy_market_order(market, price)
            
            # 호출 결과 로깅
            if result:
                log.log('TR', f"매수 API 호출 성공 - 결과: {result}")
            else:
                log.log('WA', f"매수 API 호출 결과가 None입니다.")
                
            return result
        except Exception as e:
            # 상세 오류 정보 로깅
            if hasattr(log, 'detailed_error'):
                log.detailed_error(f"시장가 매수 중 오류 (market={market}, price={price})", e)
            else:
                log.log('WA', f"시장가 매수 중 오류: {str(e)}, 타입: {type(e).__name__}, market={market}, price={price}")
            return None
    
    def sell_market_order(self, market=None, volume=None):
        """시장가 매도"""
        try:
            market = market or self.market
            
            # market과 volume 순서가 바뀐 경우 처리
            if isinstance(market, (int, float)) and isinstance(volume, str):
                log.log('WA', f"매개변수 순서가 바뀐 것으로 보입니다. 자동 교정: market={volume}, volume={market}")
                market, volume = volume, market
            
            # 타입 확인 및 변환
            if volume is None:
                error_msg = "매도 수량(volume)이 지정되지 않았습니다."
                log.log('WA', error_msg)
                raise ValueError(error_msg)
            
            # 숫자 타입으로 변환
            if isinstance(volume, str):
                try:
                    volume = float(volume)
                except ValueError as e:
                    error_msg = f"유효하지 않은 수량 형식: {volume}"
                    log.log('WA', error_msg)
                    raise ValueError(error_msg) from e
            
            log.log('TR', f"시장가 매도 시도: {market}, {volume}개")
            
            # 매개변수 출력 (디버깅용)
            log.log('TR', f"매도 API 호출 매개변수: market={market}, volume={volume}, 타입: market={type(market).__name__}, volume={type(volume).__name__}")
            
            # 실제 API 호출
            result = self.exchange.sell_market_order(market, volume)
            
            # 호출 결과 로깅
            if result:
                log.log('TR', f"매도 API 호출 성공 - 결과: {result}")
            else:
                log.log('WA', f"매도 API 호출 결과가 None입니다.")
                
            return result
        except Exception as e:
            # 상세 오류 정보 로깅
            if hasattr(log, 'detailed_error'):
                log.detailed_error(f"시장가 매도 중 오류 (market={market}, volume={volume})", e)
            else:
                log.log('WA', f"시장가 매도 중 오류: {str(e)}, 타입: {type(e).__name__}, market={market}, volume={volume}")
            return None
    
    def get_orders(self, market=None, state="wait"):
        """미체결 주문 조회"""
        try:
            market = market or self.market
            orders = self.exchange.get_order(market, state=state)
            # 반환 값이 None인 경우 빈 리스트 반환
            if orders is None:
                return []
            return orders
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
            if not orders:
                log.log('TR', f"{market} 취소할 미체결 주문이 없습니다.")
                return
                
            if isinstance(orders, list):
                for order in orders:
                    if 'uuid' in order:
                        self.cancel_order(order['uuid'])
            elif isinstance(orders, dict) and 'uuid' in orders:
                self.cancel_order(orders['uuid'])
        except Exception as e:
            log.log('WA', f"미체결 주문 취소 중 오류: {str(e)}")
    
    def cancel_all_orders(self):
        """모든 미체결 주문 취소"""
        try:
            orders = self.get_orders(self.market)
            if not orders:
                log.log('TR', "취소할 미체결 주문이 없습니다.")
                return
                
            if isinstance(orders, list):
                for order in orders:
                    if 'uuid' in order:
                        self.cancel_order(order['uuid'])
            elif isinstance(orders, dict) and 'uuid' in orders:
                self.cancel_order(orders['uuid'])
        except Exception as e:
            log.log('WA', f"전체 미체결 주문 취소 중 오류: {str(e)}") 