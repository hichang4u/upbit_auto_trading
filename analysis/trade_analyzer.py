import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import sys
sys.path.append('.')
from config.config import Config
import os
from utils.logger import log
import re

class TradeAnalyzer:
    def __init__(self):
        self.results_dir = 'analysis/results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def create_report(self, days=30):
        """코인별 거래 분석 리포트 생성"""
        try:
            reports = {}
            for coin_ticker in ['XRP']:  # 추후 다른 코인 추가 가능
                coin_stats = self.analyze_coin(coin_ticker, days)
                if coin_stats:
                    reports[coin_ticker] = {
                        'statistics': coin_stats,
                        'suggestions': self.suggest_parameters(coin_ticker, coin_stats)
                    }
                    
                    # 코인별 결과 저장
                    self.save_analysis_results(coin_ticker, reports[coin_ticker])
                    
            return reports
            
        except Exception as e:
            log.log('WA', f"분석 리포트 생성 중 오류: {str(e)}")
            return None
    
    def analyze_coin(self, coin_ticker, days):
        """개별 코인 분석"""
        try:
            # 거래 기록 로드
            trades_df = self.load_trade_history(coin_ticker, days)
            if trades_df.empty:
                return None
                
            stats = {
                'total_trades': len(trades_df),
                'win_rate': len(trades_df[trades_df['profit'] > 0]) / len(trades_df) * 100,
                'avg_profit': trades_df['profit'].mean(),
                'max_profit': trades_df['profit'].max(),
                'max_loss': trades_df['profit'].min(),
                'profit_std': trades_df['profit'].std(),
                'avg_holding_time': self.calculate_avg_holding_time(trades_df),
                'best_trading_hours': self.analyze_trading_hours(trades_df),
                'volume_profit_correlation': self.analyze_volume_correlation(trades_df)
            }
            
            return stats
            
        except Exception as e:
            log.log('WA', f"{coin_ticker} 분석 중 오류: {str(e)}")
            return None
    
    def suggest_parameters(self, coin_ticker, stats):
        """코인별 파라미터 제안"""
        try:
            if coin_ticker == 'XRP':
                from config.coins.xrp_config import XRPConfig as CoinConfig
            # elif coin_ticker == 'BTC':
            #     from config.coins.btc_config import BTCConfig as CoinConfig
            
            suggestions = {}
            
            # 수익률 기반 제안
            suggestions['PROFIT_RATE'] = min(stats['avg_profit'] * 0.8, 0.05)
            suggestions['LOSS_RATE'] = min(abs(stats['max_loss']) * 1.2, 0.05)
            
            # 변동성 기반 제안
            suggestions['VOLATILITY_FACTOR'] = self.calculate_volatility_factor(stats)
            
            # 거래량 기반 제안
            suggestions['VOLUME_SURGE_THRESHOLD'] = self.calculate_volume_threshold(stats)
            
            # 볼린저 밴드 기반 제안
            suggestions['BB_WIDTH'] = self.calculate_bb_width(stats)
            
            return suggestions
            
        except Exception as e:
            log.log('WA', f"{coin_ticker} 파라미터 제안 중 오류: {str(e)}")
            return None
    
    def save_analysis_results(self, coin_ticker, results):
        """코인별 분석 결과 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"{self.results_dir}/{coin_ticker}_analysis_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
                
            log.log('TR', f"{coin_ticker} 분석 결과가 저장되었습니다: {filename}")
            
        except Exception as e:
            log.log('WA', f"{coin_ticker} 분석 결과 저장 중 오류: {str(e)}")

    def load_trade_history(self, coin_ticker, days=30):
        """거래 기록 로드"""
        try:
            # 로그 파일들을 날짜순으로 정렬하여 로드
            log_dir = 'logs'
            trade_data = []
            
            # 분석 기간 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 로그 파일 검색
            log_files = []
            for filename in os.listdir(log_dir):
                if filename.startswith('trading_') and filename.endswith('.log'):
                    file_date = datetime.strptime(filename[8:16], '%Y%m%d')
                    if start_date <= file_date <= end_date:
                        log_files.append(os.path.join(log_dir, filename))
            
            # 각 로그 파일에서 거래 기록 추출
            for log_file in sorted(log_files):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if f'KRW-{coin_ticker}' in line:
                            trade_info = self.parse_trade_log(line, coin_ticker)
                            if trade_info:
                                trade_data.append(trade_info)
            
            # DataFrame 생성
            if trade_data:
                df = pd.DataFrame(trade_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                return df
            
            return pd.DataFrame()  # 빈 DataFrame 반환
            
        except Exception as e:
            log.log('WA', f"{coin_ticker} 거래 기록 로드 중 오류: {str(e)}")
            return pd.DataFrame()

    def parse_trade_log(self, log_line, coin_ticker):
        """로그 라인 파싱"""
        try:
            # 로그 형식: LEVEL|TIMESTAMP|MESSAGE
            parts = log_line.strip().split('|')
            if len(parts) != 3:
                return None
            
            level, timestamp, message = parts
            
            # 매수/매도 거래 기록 파싱
            if f'KRW-{coin_ticker}' in message:
                trade_info = {
                    'timestamp': timestamp,
                    'market': f'KRW-{coin_ticker}',
                    'type': None,
                    'price': None,
                    'amount': None,
                    'profit': None
                }
                
                # 매수 기록
                if '매수' in message:
                    trade_info['type'] = 'BUY'
                    # 가격 추출
                    price_match = re.search(r'매수�가: ([\d,]+)원', message)
                    if price_match:
                        trade_info['price'] = float(price_match.group(1).replace(',', ''))
                    # 수량 추출
                    amount_match = re.search(r'매수�량: ([\d.]+)', message)
                    if amount_match:
                        trade_info['amount'] = float(amount_match.group(1))
                    
                # 매도 기록
                elif '매도' in message:
                    trade_info['type'] = 'SELL'
                    # 가격 추출
                    price_match = re.search(r'매도�가: ([\d,]+)원', message)
                    if price_match:
                        trade_info['price'] = float(price_match.group(1).replace(',', ''))
                    # 수량 추출
                    amount_match = re.search(r'매도�량: ([\d.]+)', message)
                    if amount_match:
                        trade_info['amount'] = float(amount_match.group(1))
                    # 수익률 추출
                    profit_match = re.search(r'거�수익: ([+-]?\d+\.?\d*)%', message)
                    if profit_match:
                        trade_info['profit'] = float(profit_match.group(1))
                
                if trade_info['price'] is not None and trade_info['amount'] is not None:
                    return trade_info
                
            return None
            
        except Exception as e:
            log.log('WA', f"로그 �싱 중 오류: {str(e)}")
            return None

    def calculate_avg_holding_time(self, df):
        """평균 보유 시간 계산"""
        try:
            if df.empty or 'type' not in df.columns:
                return 0
            
            holding_times = []
            buy_time = None
            
            for _, row in df.iterrows():
                if row['type'] == 'BUY':
                    buy_time = row['timestamp']
                elif row['type'] == 'SELL' and buy_time is not None:
                    holding_time = (row['timestamp'] - buy_time).total_seconds() / 3600  # 시간 단위
                    holding_times.append(holding_time)
                    buy_time = None
            
            return np.mean(holding_times) if holding_times else 0
            
        except Exception as e:
            log.log('WA', f"평균 보유 시간 계산 중 오류: {str(e)}")
            return 0

    def analyze_trading_hours(self, df):
        """거래 시간대 분석"""
        try:
            if df.empty or 'timestamp' not in df.columns:
                return []
            
            # 수익이 발생한 거래만 필터링
            profit_trades = df[df['profit'] > 0]
            
            if profit_trades.empty:
                return []
            
            # 시간대별 수익률 평균 계산
            profit_trades['hour'] = profit_trades['timestamp'].dt.hour
            hourly_profits = profit_trades.groupby('hour')['profit'].mean()
            
            # 상위 3개 시간대 반환
            best_hours = hourly_profits.nlargest(3)
            return best_hours.index.tolist()
            
        except Exception as e:
            log.log('WA', f"거래 시간대 분석 중 오류: {str(e)}")
            return []

    def analyze_volume_correlation(self, df):
        """거래량과 수익률의 상관관계 분석"""
        try:
            if df.empty or 'profit' not in df.columns or 'amount' not in df.columns:
                return 0
            
            return df['profit'].corr(df['amount'])
            
        except Exception as e:
            log.log('WA', f"거래량과 수익률 상관관계 분석 중 오류: {str(e)}")
            return 0

def main():
    analyzer = TradeAnalyzer()
    report = analyzer.create_report()
    
    if report:
        print("\n=== 거래 분석 리포트 ===")
        print(f"분석 기간: {report['period']}")
        print("\n[거래 통계]")
        stats = report['statistics']
        print(f"총 거래 횟수: {stats['total_trades']}")
        print(f"승률: {stats['win_rate']:.2f}%")
        print(f"평균 수익률: {stats['avg_profit']:.2f}%")
        print(f"최대 수익률: {stats['max_profit']:.2f}%")
        print(f"최대 손실률: {stats['max_loss']:.2f}%")
        
        print("\n[파라미터 제안]")
        for param, value in report['suggestions'].items():
            print(f"{param}: {value:.4f}")

if __name__ == "__main__":
    main() 