import signal
import sys
import schedule
import threading
import time
from datetime import datetime, time as datetime_time
from src.api_client import UpbitClient
from src.strategies.xrp_strategy import XRPStrategy
from src.trader import MultiCoinTrader
from analysis.trade_analyzer import TradeAnalyzer
from utils.logger import log
from config.config import Config
from config.coins.xrp_config import XRPConfig

def signal_handler(signum, frame):
    """종료 시그널 처리"""
    log.log('TR', "\n프로그램 종료 신호를 받았습니다.")
    if 'trader' in globals():
        trader.stop()
    sys.exit(0)

def run_analysis():
    """정기 분석 실행"""
    try:
        log.print_header("일일 거래 분석 시작")
        analyzer = TradeAnalyzer()
        report = analyzer.create_report(days=Config.ANALYSIS_DAYS)
        
        if report and report['statistics']['total_trades'] > 0:
            stats = report['statistics']
            log.log('TR', f"총 거래 횟수: {stats['total_trades']}")
            log.log('TR', f"승률: {stats['win_rate']:.2f}%")
            log.log('TR', f"평균 수익률: {stats['avg_profit']:.2f}%")
            
            if Config.AUTO_ADJUST_PARAMS:
                suggestions = report['suggestions']
                for coin in trader.traders.keys():
                    coin_config = trader.traders[coin]['config']
                    for param, value in suggestions.items():
                        if hasattr(coin_config, param):
                            old_value = getattr(coin_config, param)
                            setattr(coin_config, param, value)
                            log.log('TR', f"{coin} 파라미터 조정: {param} {old_value:.4f} -> {value:.4f}")
                
                trader.initialize_traders()
                log.log('TR', "거래 전략 파라미터가 업데이트되었습니다.")
        
    except Exception as e:
        log.log('WA', f"분석 중 오류 발생: {str(e)}")

def schedule_analysis():
    """분석 스케줄러"""
    while True:
        now = datetime.now().time()
        analysis_time = datetime.strptime(Config.ANALYSIS_TIME, '%H:%M').time()
        
        if now.hour == analysis_time.hour and now.minute == analysis_time.minute:
            run_analysis()
            time.sleep(60)
        time.sleep(30)

def is_trading_time():
    """거래 가능 시간 확인"""
    now = datetime.now().time()
    start = datetime_time(Config.TRADING_START_HOUR, 0)
    end = datetime_time(Config.TRADING_END_HOUR, 0)
    
    if start <= end:
        return start <= now <= end
    else:
        return now >= start or now <= end

def main():
    try:
        # 종료 시그널 핸들러 등록
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        mode = "시뮬레이션" if Config.SIMULATION_MODE else "실제 거래"
        log.print_header("설정 정보")
        log.log('TR', f"실행 모드: {mode}")
        
        # 분석 스레드 시작
        if Config.ENABLE_ANALYSIS:
            analysis_thread = threading.Thread(target=schedule_analysis, daemon=True)
            analysis_thread.start()
            log.log('TR', f"자동 분석 스케줄러 시작 (매일 {Config.ANALYSIS_TIME})")
        
        # 트레이더 초기화 및 시작
        global trader
        trader = MultiCoinTrader()
        
        # 초기 분석 실행
        if Config.ENABLE_ANALYSIS:
            run_analysis()
        
        # 자동매매 시작 (24시간 연속 거래)
        trader.start()
        
    except Exception as e:
        log.log('WA', f"프로그램 실행 중 오류 발생: {str(e)}")
        if 'trader' in globals():
            trader.stop()
        sys.exit(1)

if __name__ == "__main__":
    main() 