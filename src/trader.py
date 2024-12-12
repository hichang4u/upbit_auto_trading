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
            
            if Config.SIMULATION_MODE:
                avg_price = trader['simulation_entry_price']
            else:
                # avg_buy_price가 직접 전달되지 않은 경우에만 API 호출
                if avg_buy_price is None:
                    avg_price = trader['client'].get_avg_buy_price(trader['config'].COIN_TICKER)
                else:
                    avg_price = avg_buy_price
                
            # 숫자형으로 변환 (API가 문자열을 반환할 수 있음)
            if avg_price is not None:
                avg_price = float(avg_price)
                
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
            current_price = trader['client'].get_current_price(trader['config'].MARKET)
            
            # 현재가가 None이면 종료
            if current_price is None:
                log.log('WA', f"{coin_ticker} 현재가 조회 실패")
                return None, None, None
                
            if Config.SIMULATION_MODE:
                balance = trader['simulation_balance']
                cash_balance = balance['KRW']
                coin_balance = balance[trader['config'].COIN_TICKER]
            else:
                # 현금 잔고와 코인 잔고를 개별적으로 조회
                cash_balance = trader['client'].get_balance('KRW') or 0
                coin_balance = trader['client'].get_balance(trader['config'].COIN_TICKER) or 0
            
            profit_amount, profit_rate, avg_buy_price = self.get_profit_info(
                coin_ticker, current_price, coin_balance
            )
            
            mode = "[시뮬레이션]" if Config.SIMULATION_MODE else "[실제 거래]"
            log.print_section(f"{mode} {coin_ticker} 현재 상태")
            log.log('TR', f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log.log('TR', f"현재가: {current_price:,}원")
            log.log('TR', f"보유현금: {cash_balance:,}원")
            log.log('TR', f"보유코인: {coin_balance:.4f} {trader['config'].COIN_TICKER}")
            
            if coin_balance > 0:
                log.log('TR', f"평균단가: {avg_buy_price:,}원")
                log.log('TR', f"평가손익: {int(profit_amount):,}원 ({profit_rate:+.2f}%)")
            
            return current_price, cash_balance, coin_balance
                
        except Exception as e:
            log.log('WA', f"{coin_ticker} 정보 출력 중 오류: {str(e)}")
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
            balance = trader['simulation_balance'] if Config.SIMULATION_MODE else trader['client'].get_balance()
            
            # API 호출 제한 확인
            self.check_api_rate_limit()
            
            # 거래 신호 확인
            signal = trader['strategy'].get_trading_signal(trader['config'].MARKET)
            self.record_api_call()
            
            if signal == 'BUY':
                cash_balance = balance['KRW']
                trade_amount = min(cash_balance, trader['config'].TRADE_UNIT)
                
                if trade_amount >= 5000:  # 최소 주문금액
                    if Config.SIMULATION_MODE:
                        return self.simulate_market_buy(coin_ticker, trade_amount)
                    else:
                        return trader['client'].buy_market_order(trader['config'].MARKET, trade_amount)
                        
            elif signal == 'SELL':
                coin_balance = balance[trader['config'].COIN_TICKER]
                if coin_balance > 0:
                    if Config.SIMULATION_MODE:
                        return self.simulate_market_sell(coin_ticker, coin_balance)
                    else:
                        return trader['client'].sell_market_order(trader['config'].MARKET, coin_balance)
                        
        except Exception as e:
            log.log('WA', f"{coin_ticker} 매매 실행 중 오류: {str(e)}")
        return False
    
    def start(self):
        """모든 코인 트레이딩 시작"""
        try:
            self.is_running = True
            if not Config.SIMULATION_MODE:
                for trader in self.traders.values():
                    trader['client'].cancel_all_orders()
            
            mode = "시뮬레이션" if Config.SIMULATION_MODE else "실제 거래"
            log.print_header(f"자동매매 프로그램 시작 ({mode})")
            
            for coin_ticker, trader in self.traders.items():
                log.log('TR', f"{coin_ticker} 거래 시작")
                log.log('TR', f"대상: {trader['config'].MARKET}")
                if Config.SIMULATION_MODE:
                    log.log('TR', f"초기자금: {trader['simulation_balance']['KRW']:,}원")
                log.log('TR', f"매매단위: {trader['config'].TRADE_UNIT:,}원")
            
            while self.is_running:
                for coin_ticker in self.traders.keys():
                    try:
                        current_price, cash_balance, coin_balance = self.print_trading_info(coin_ticker)
                        if None in (current_price, cash_balance, coin_balance):
                            continue
                        
                        self.execute_trade(coin_ticker)
                        
                    except Exception as e:
                        log.log('WA', f"{coin_ticker} 거래 중 오류 발생: {str(e)}")
                
                time.sleep(Config.TRADE_INTERVAL)
                    
        except KeyboardInterrupt:
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
