import time
from datetime import datetime
from collections import deque
from utils.logger import log
from config.config import Config
from src.api_client import UpbitClient

class MultiCoinTrader:
    def __init__(self):
        self.traders = {}
        self.api_calls = deque(maxlen=600)  # 최근 600개의 API 호출 시간 기록
        self.last_api_call = None
        self.is_running = False
        self.initialize_traders()
        
    def initialize_traders(self):
        """코인별 트레이더 초기화"""
        try:
            # XRP 트레이더
            from src.strategies.xrp_strategy import XRPStrategy
            from config.coins.xrp_config import XRPConfig
            
            strategy = XRPStrategy()
            client = UpbitClient()  # API 클라이언트 생성
            strategy.set_client(client)  # 전에 클라이언트 주입
            
            self.traders['XRP'] = {
                'strategy': strategy,
                'config': XRPConfig,
                'client': client,
                'simulation_balance': {
                    'KRW': Config.SIMULATION_CASH,
                    XRPConfig.COIN_TICKER: 0
                },
                'simulation_entry_price': 0
            }
            
            log.log('TR', f"XRP 트레이더 초기화 완료")
            
        except Exception as e:
            log.log('WA', f"트레이더 초기화 중 오류: {str(e)}")
    
    def check_api_rate_limit(self):
        """API 호출 제한 확인"""
        now = datetime.now()
        
        # 1분 이상 지난 호출 기록 제거
        while self.api_calls and (now - self.api_calls[0]).total_seconds() > 60:
            self.api_calls.popleft()
        
        # 분당 최대 호출 수 확인
        if len(self.api_calls) >= Config.MAX_API_CALLS:
            wait_time = 60 - (now - self.api_calls[0]).total_seconds()
            if wait_time > 0:
                log.log('TR', f"API 호출 제한 대기: {wait_time:.1f}초")
                time.sleep(wait_time)
    
    def record_api_call(self):
        """API 호출 기록"""
        now = datetime.now()
        self.api_calls.append(now)
        self.last_api_call = now
    
    def get_profit_info(self, coin_ticker, current_price, coin_balance, avg_buy_price=None):
        """수익률 및 평가손익 계산"""
        try:
            trader = self.traders[coin_ticker]
            
            # 숫자 타입으로 변환
            try:
                current_price = float(current_price)
                coin_balance = float(coin_balance)
            except (TypeError, ValueError):
                log.log('WA', f"{coin_ticker} 수익률 계산 중 타입 변환 오류 (현재가: {current_price}, 코인잔고: {coin_balance})")
                return 0, 0, 0
            
            if Config.SIMULATION_MODE:
                avg_price = trader['simulation_entry_price']
            else:
                # avg_buy_price가 직접 전달되지 않은 경우에만 API 호출
                if avg_buy_price is None:
                    avg_price = trader['client'].get_avg_buy_price(trader['config'].COIN_TICKER)
                else:
                    avg_price = avg_buy_price
                
            # 숫자형으로 변환 (API가 문자열을 반환할 수 있음)
            try:
                if avg_price is not None:
                    avg_price = float(avg_price)
            except (TypeError, ValueError):
                log.log('WA', f"{coin_ticker} 평균 매수가 변환 오류: {avg_price}")
                avg_price = 0
                
            if avg_price and coin_balance > 0:
                profit_rate = ((current_price - avg_price) / avg_price) * 100
                profit_amount = coin_balance * avg_price * (profit_rate / 100)
                return profit_amount, profit_rate, avg_price
            return 0, 0, 0
            
        except Exception as e:
            log.log('WA', f"{coin_ticker} 수익률 계산 중 오류: {str(e)}")
            return 0, 0, 0
    
    def print_trading_info(self, coin_ticker):
        """거래 정보 출력"""
        try:
            trader = self.traders[coin_ticker]
            
            # 현재가 조회
            try:
                current_price = trader['client'].get_current_price(trader['config'].MARKET)
                
                # 현재가가 None이면 종료
                if current_price is None:
                    log.log('WA', f"{coin_ticker} 현재가 조회 실패")
                    return None, None, None
            except Exception as e:
                log.detailed_error(f"{coin_ticker} 현재가 조회 중 오류", e)
                return None, None, None
                
            # 잔고 정보 조회
            try:
                if Config.SIMULATION_MODE:
                    balance = trader['simulation_balance']
                    cash_balance = balance.get('KRW', 0)
                    coin_balance = balance.get(trader['config'].COIN_TICKER, 0)
                else:
                    # 현금 잔고와 코인 잔고를 개별적으로 조회
                    try:
                        cash_balance = trader['client'].get_balance('KRW')
                        if cash_balance is None:
                            log.log('WA', f"{coin_ticker} 현금 잔고 조회 실패")
                            cash_balance = 0
                    except Exception as e:
                        log.detailed_error(f"{coin_ticker} 현금 잔고 조회 중 오류", e)
                        cash_balance = 0
                    
                    try:
                        coin_balance = trader['client'].get_balance(trader['config'].COIN_TICKER)
                        if coin_balance is None:
                            log.log('WA', f"{coin_ticker} 코인 잔고 조회 실패")
                            coin_balance = 0
                    except Exception as e:
                        log.detailed_error(f"{coin_ticker} 코인 잔고 조회 중 오류", e)
                        coin_balance = 0
                    
                # 숫자 타입으로 변환
                try:
                    cash_balance = float(cash_balance)
                    coin_balance = float(coin_balance)
                except (TypeError, ValueError) as e:
                    log.detailed_error(f"{coin_ticker} 잔고 정보 변환 오류", e)
                    cash_balance = 0
                    coin_balance = 0
            except Exception as e:
                log.detailed_error(f"{coin_ticker} 잔고 정보 조회 중 오류", e)
                cash_balance = 0
                coin_balance = 0
            
            # 수익 정보 계산
            try:
                profit_amount, profit_rate, avg_buy_price = self.get_profit_info(
                    coin_ticker, current_price, coin_balance
                )
            except Exception as e:
                log.detailed_error(f"{coin_ticker} 수익 정보 계산 오류", e)
                profit_amount, profit_rate, avg_buy_price = 0, 0, 0
            
            # 정보 출력
            try:
                mode = "[시뮬레이션]" if Config.SIMULATION_MODE else "[실제 거래]"
                log.print_section(f"{mode} {coin_ticker} 현재 상태")
                log.log('TR', f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                log.log('TR', f"현재가: {current_price:,}원")
                log.log('TR', f"보유현금: {cash_balance:,}원")
                log.log('TR', f"보유코인: {coin_balance:.4f} {trader['config'].COIN_TICKER}")
                
                if coin_balance > 0 and avg_buy_price > 0:
                    log.log('TR', f"평균단가: {avg_buy_price:,}원")
                    log.log('TR', f"평가손익: {int(profit_amount):,}원 ({profit_rate:+.2f}%)")
            except Exception as e:
                log.detailed_error(f"{coin_ticker} 거래 정보 출력 중 화면 출력 오류", e)
            
            return current_price, cash_balance, coin_balance
                
        except Exception as e:
            log.detailed_error(f"{coin_ticker} 정보 출력 중 오류", e)
            return None, None, None
    
    def simulate_market_buy(self, coin_ticker, amount):
        """시뮬레이션 매수"""
        trader = self.traders[coin_ticker]
        current_price = trader['client'].get_current_price(trader['config'].MARKET)
        if current_price:
            coin_amount = amount / current_price
            if trader['simulation_balance']['KRW'] >= amount:
                trader['simulation_balance']['KRW'] -= amount
                trader['simulation_balance'][trader['config'].COIN_TICKER] += coin_amount
                trader['simulation_entry_price'] = current_price
                
                log.print_section(f"{coin_ticker} 매수 체결 완료")
                log.log('TR', f"매수금액: {amount:,}원")
                log.log('TR', f"매수단가: {current_price:,}원")
                log.log('TR', f"매수수량: {coin_amount:.4f} {trader['config'].COIN_TICKER}")
                return True
        return False
    
    def simulate_market_sell(self, coin_ticker, coin_amount):
        """시뮬레이션 매도"""
        trader = self.traders[coin_ticker]
        current_price = trader['client'].get_current_price(trader['config'].MARKET)
        if current_price and trader['simulation_balance'][trader['config'].COIN_TICKER] >= coin_amount:
            amount = coin_amount * current_price
            trader['simulation_balance']['KRW'] += amount
            trader['simulation_balance'][trader['config'].COIN_TICKER] -= coin_amount
            profit_rate = ((current_price / trader['simulation_entry_price']) - 1) * 100
            
            log.print_section(f"{coin_ticker} 매도 체결 완료")
            log.log('TR', f"매도수량: {coin_amount:.4f} {trader['config'].COIN_TICKER}")
            log.log('TR', f"매도단가: {current_price:,}원")
            log.log('TR', f"매도금액: {amount:,}원")
            log.log('TR', f"거래수익: {profit_rate:+.2f}%")
            return True
        return False
    
    def execute_trade(self, coin_ticker):
        """매매 실행"""
        try:
            trader = self.traders[coin_ticker]
            
            # API 호출 제한 확인
            self.check_api_rate_limit()
            
            # 거래 신호 확인
            try:
                signal = trader['strategy'].get_trading_signal(trader['config'].MARKET)
                self.record_api_call()
            except Exception as e:
                log.detailed_error(f"{coin_ticker} 거래 신호 확인 중 오류", e)
                return False
            
            if signal == 'BUY':
                # 시뮬레이션 모드
                if Config.SIMULATION_MODE:
                    try:
                        cash_balance = trader['simulation_balance'].get('KRW', 0)
                        trade_amount = min(cash_balance, trader['config'].TRADE_UNIT)
                        
                        if trade_amount >= 5000:  # 최소 주문금액
                            return self.simulate_market_buy(coin_ticker, trade_amount)
                    except Exception as e:
                        log.detailed_error(f"{coin_ticker} 시뮬레이션 매수 처리 중 오류", e)
                        return False
                # 실제 거래 모드
                else:
                    # 현금 잔고 조회
                    try:
                        cash_balance = trader['client'].get_balance('KRW')
                        if cash_balance is None:
                            log.log('WA', f"{coin_ticker} 현금 잔고 조회 실패")
                            return False
                        
                        try:
                            cash_balance = float(cash_balance)
                        except (TypeError, ValueError) as e:
                            log.detailed_error(f"{coin_ticker} 현금 잔고 타입 변환 오류: {cash_balance}", e)
                            return False
                        
                        trade_amount = min(cash_balance, trader['config'].TRADE_UNIT)
                        
                        if trade_amount >= 5000:  # 최소 주문금액
                            try:
                                # 매개변수 순서 주의: 마켓, 금액
                                log.log('TR', f"{coin_ticker} 매수 시도: {trade_amount:,}원")
                                result = trader['client'].buy_market_order(
                                    market=trader['config'].MARKET, 
                                    price=trade_amount
                                )
                                if result:
                                    log.log('TR', f"{coin_ticker} 매수 주문 성공: {trade_amount:,}원")
                                else:
                                    log.log('WA', f"{coin_ticker} 매수 주문 실패: 결과가 None")
                                return result
                            except Exception as e:
                                log.detailed_error(f"{coin_ticker} 매수 주문 중 오류: 금액={trade_amount}", e)
                                return False
                        else:
                            log.log('TR', f"{coin_ticker} 최소 주문금액 미달: {trade_amount:,}원")
                    except Exception as e:
                        log.detailed_error(f"{coin_ticker} 매수 처리 중 오류", e)
                        return False
                        
            elif signal == 'SELL':
                # 시뮬레이션 모드
                if Config.SIMULATION_MODE:
                    try:
                        coin_balance = trader['simulation_balance'].get(trader['config'].COIN_TICKER, 0)
                        if coin_balance > 0:
                            return self.simulate_market_sell(coin_ticker, coin_balance)
                    except Exception as e:
                        log.detailed_error(f"{coin_ticker} 시뮬레이션 매도 처리 중 오류", e)
                        return False
                # 실제 거래 모드
                else:
                    # 코인 잔고 조회
                    try:
                        coin_balance = trader['client'].get_balance(trader['config'].COIN_TICKER)
                        if coin_balance is None:
                            log.log('WA', f"{coin_ticker} 코인 잔고 조회 실패")
                            return False
                        
                        try:
                            coin_balance = float(coin_balance)
                        except (TypeError, ValueError) as e:
                            log.detailed_error(f"{coin_ticker} 코인 잔고 타입 변환 오류: {coin_balance}", e)
                            return False
                        
                        if coin_balance > 0:
                            try:
                                # 매개변수 순서 주의: 마켓, 수량
                                log.log('TR', f"{coin_ticker} 매도 시도: {coin_balance} {trader['config'].COIN_TICKER}")
                                result = trader['client'].sell_market_order(
                                    market=trader['config'].MARKET, 
                                    volume=coin_balance
                                )
                                if result:
                                    log.log('TR', f"{coin_ticker} 매도 주문 성공: {coin_balance} {trader['config'].COIN_TICKER}")
                                else:
                                    log.log('WA', f"{coin_ticker} 매도 주문 실패: 결과가 None")
                                return result
                            except Exception as e:
                                log.detailed_error(f"{coin_ticker} 매도 주문 중 오류: 수량={coin_balance}", e)
                                return False
                        else:
                            log.log('TR', f"{coin_ticker} 매도할 코인이 없습니다")
                    except Exception as e:
                        log.detailed_error(f"{coin_ticker} 매도 처리 중 오류", e)
                        return False
                        
        except Exception as e:
            log.detailed_error(f"{coin_ticker} 매매 실행 중 오류", e)
        return False
    
    def start(self):
        """모든 코인 트레이더 시작"""
        try:
            self.is_running = True
            
            # 기존 미체결 주문 취소
            if not Config.SIMULATION_MODE:
                try:
                    for coin_ticker, trader in self.traders.items():
                        try:
                            trader['client'].cancel_all_orders()
                        except Exception as e:
                            log.detailed_error(f"{coin_ticker} 미체결 주문 취소 실패", e)
                except Exception as e:
                    log.detailed_error("미체결 주문 취소 중 오류", e)
            
            mode = "시뮬레이션" if Config.SIMULATION_MODE else "실제 거래"
            log.print_header(f"자동매매 프로그램 시작 ({mode})")
            
            # 각 코인별 트레이더 정보 출력
            for coin_ticker, trader in self.traders.items():
                try:
                    log.log('TR', f"{coin_ticker} 거래 시작")
                    log.log('TR', f"대상: {trader['config'].MARKET}")
                    
                    # 시뮬레이션 모드에서 초기 자금 출력
                    if Config.SIMULATION_MODE:
                        try:
                            krw_balance = trader['simulation_balance'].get('KRW', 0)
                            log.log('TR', f"초기자금: {krw_balance:,}원")
                        except Exception as e:
                            log.detailed_error(f"{coin_ticker} 초기 자금 확인 실패", e)
                    
                    # TRADE_UNIT 값 확인 및 출력
                    try:
                        trade_unit = getattr(trader['config'], 'TRADE_UNIT', None)
                        if trade_unit is not None:
                            trade_unit = float(trade_unit)
                            log.log('TR', f"매매단위: {trade_unit:,}원")
                        else:
                            log.log('WA', f"{coin_ticker} 설정에 매매단위(TRADE_UNIT)가 없습니다")
                    except (TypeError, ValueError, AttributeError) as e:
                        log.detailed_error(f"{coin_ticker} 매매단위 확인 실패", e)
                        
                except Exception as e:
                    log.detailed_error(f"{coin_ticker} 정보 출력 중 오류", e)
            
            # 메인 거래 루프
            while self.is_running:
                for coin_ticker in list(self.traders.keys()):
                    try:
                        # 현재 상태 출력 및 거래 실행
                        try:
                            current_price, cash_balance, coin_balance = self.print_trading_info(coin_ticker)
                        except Exception as e:
                            log.detailed_error(f"{coin_ticker} 거래 정보 출력 중 오류", e)
                            continue
                            
                        if None in (current_price, cash_balance, coin_balance):
                            log.log('WA', f"{coin_ticker} 거래 정보 누락 (현재가: {current_price}, 현금: {cash_balance}, 코인: {coin_balance})")
                            continue
                            
                        # 거래 실행
                        try:
                            self.execute_trade(coin_ticker)
                        except Exception as e:
                            log.detailed_error(f"{coin_ticker} 거래 실행 중 오류", e)
                        
                    except Exception as e:
                        log.detailed_error(f"{coin_ticker} 거래 중 오류 발생", e)
                
                time.sleep(Config.TRADE_INTERVAL)
                    
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            log.detailed_error("트레이더 실행 중 예상치 못한 오류", e)
            self.stop()
            
    def stop(self):
        """거래 중지"""
        self.is_running = False
        log.print_header("프로그램 종료")
        
        if not Config.SIMULATION_MODE:
            for coin_ticker, trader in self.traders.items():
                trader['client'].cancel_all_orders()
                if Config.SELL_ALL_ON_STOP:
                    balance = trader['client'].get_balance()
                    coin_balance = balance.get(trader['config'].COIN_TICKER, 0)
                    if coin_balance > 0:
                        trader['client'].sell_market_order(trader['config'].MARKET, coin_balance)
                        log.log('TR', f"{coin_ticker} 보유 코인 전량 매도: {coin_balance} {trader['config'].COIN_TICKER}")
        
        # 최종 거래 정보 출력
        for coin_ticker in self.traders.keys():
            self.print_trading_info(coin_ticker)
        
        mode = "시뮬레이션" if Config.SIMULATION_MODE else "실제 거래"
        log.log('TR', f"{mode} 모드 프로그램이 안전하게 종료되었습니다")
    
    def print_info(self, data):
        """거래 정보 출력"""
        try:
            # 현재가가 단순 정수인 경우
            if isinstance(data, (int, float)):
                log.log('TR', f"현재가: {data:,.0f} 원")
                return

            # 리스트인 경우
            if isinstance(data, list):
                if len(data) > 0:
                    info = data[0]
                else:
                    log.log('TR', "거래 정보가 없습니다")
                    return
            # 딕셔너리인 경우
            elif isinstance(data, dict):
                info = data
            else:
                log.log('WA', f"예상치 못한 데이터 형식: {type(data)}")
                return

            # 딕셔너리에서 정보 추출
            price = info.get('trade_price', 0)
            volume = info.get('trade_volume', 0)
            log.log('TR', f"현재가: {price:,.0f} 원")
            log.log('TR', f"거래량: {volume:,.4f}")
            
        except Exception as e:
            log.log('WA', f"거래 정보 출력 중 오류: {str(e)}")
    
    def check_and_trade(self, market, strategy):
        """개별 코인 거래 실행"""
        try:
            # 매매 신호 확인
            signal = strategy.get_trading_signal(market)
            
            # 매매 실행
            if signal == 'BUY':
                self.execute_buy(market, strategy)
            elif signal == 'SELL':
                self.execute_sell(market, strategy)
                
        except Exception as e:
            log.log('WA', f"{market} 거래 처리 중 오류: {str(e)}")
            return None
