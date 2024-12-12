import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import sys
import shutil
sys.path.append('.')
from config.config import Config
import os
from utils.logger import log
import re
from utils.telegram_notifier import send_telegram_alert

class TradeAnalyzer:
    def __init__(self):
        self.results_dir = 'analysis/results'
        self.backup_dir = 'analysis/backups'
        self.history_file = 'analysis/parameter_history.json'
        self.max_adjustment_rates = {
            'PROFIT_RATE': 0.2,      # 최대 20% 조정
            'LOSS_RATE': 0.2,
            'VOLATILITY_FACTOR': 0.3,
            'VOLUME_SURGE_THRESHOLD': 0.3,
            'BB_WIDTH': 0.2,
            'MIN_VOLUME_RATIO': 0.2
        }
        
        # 필요한 디렉토리 생성
        for directory in [self.results_dir, self.backup_dir]:
            os.makedirs(directory, exist_ok=True)
            
        # 파라미터 변경 이력 초기화
        if not os.path.exists(self.history_file):
            self.save_parameter_history({})

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
                    self.save_analysis_results(coin_ticker, reports[coin_ticker])
                    
                    # 텔레그램 알림 추가
                    stats = reports[coin_ticker]['statistics']
                    analysis_msg = (
                        f"📊 {coin_ticker} 일일 거래 분석 결과\n"
                        f"총 거래 횟수: {stats['total_trades']}\n"
                        f"승률: {stats['win_rate']:.2f}%\n"
                        f"평균 수익률: {stats['avg_profit']:.2f}%\n"
                        f"최대 수익: {stats['max_profit']:.2f}%\n"
                        f"최대 손실: {stats['max_loss']:.2f}%\n"
                        f"평균 보유 시간: {stats['avg_holding_time']:.1f}시간"
                    )
                    send_telegram_alert(analysis_msg, Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)
                    
            return reports
        except Exception as e:
            log.log('WA', f"분석 리포트 생성 중 오류: {str(e)}")
            return None

    def suggest_parameters(self, coin_ticker, stats):
        """코인별 파라미터 제안 (안전 제한 적용)"""
        try:
            if coin_ticker == 'XRP':
                from config.coins.xrp_config import XRPConfig as CoinConfig
            
            current_params = self.get_current_parameters(coin_ticker)
            suggestions = {}
            
            # 수익률 기반 제안 (안전 제한 적용)
            suggestions['PROFIT_RATE'] = self.limit_adjustment(
                current_params['PROFIT_RATE'],
                min(stats['avg_profit'] * 0.8, 0.05),
                'PROFIT_RATE'
            )
            
            suggestions['LOSS_RATE'] = self.limit_adjustment(
                current_params['LOSS_RATE'],
                min(abs(stats['max_loss']) * 1.2, 0.05),
                'LOSS_RATE'
            )
            
            # 기타 파라미터 제안...
            suggestions['VOLATILITY_FACTOR'] = self.limit_adjustment(
                current_params['VOLATILITY_FACTOR'],
                self.calculate_volatility_factor(stats),
                'VOLATILITY_FACTOR'
            )
            
            return suggestions
        except Exception as e:
            log.log('WA', f"{coin_ticker} 파라미터 제안 중 오류: {str(e)}")
            return None

    def limit_adjustment(self, current_value, suggested_value, param_name):
        """파라미터 조정 제한"""
        max_rate = self.max_adjustment_rates.get(param_name, 0.2)
        min_change = current_value * (1 - max_rate)
        max_change = current_value * (1 + max_rate)
        return max(min_change, min(max_change, suggested_value))

    def update_coin_config(self, coin_ticker, suggestions):
        """분석 결과를 바탕으로 코인 설정 업데이트 (안전장치 포함)"""
        try:
            config_path = f'config/coins/{coin_ticker.lower()}_config.py'
            if not os.path.exists(config_path):
                log.log('WA', f"{config_path} 파일이 존재하지 않습니다.")
                return False
            
            # 설정 파일 백업
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.backup_dir}/{coin_ticker.lower()}_config_{timestamp}.py"
            shutil.copy2(config_path, backup_path)
            
            # 현재 설정 읽기
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = f.read()
            
            # 파라미터 변경 이력 로드
            history = self.load_parameter_history()
            if coin_ticker not in history:
                history[coin_ticker] = []
            
            # 새로운 설정으로 업데이트
            updated_config = current_config
            changes = {}
            
            for param, value in suggestions.items():
                pattern = f"{param}\s*=\s*[0-9.]+\n"
                replacement = f"{param} = {value}\n"
                if re.search(pattern, updated_config):
                    updated_config = re.sub(pattern, replacement, updated_config)
                    changes[param] = {'old': float(re.search(pattern, current_config).group().split('=')[1].strip()),
                                    'new': value}
            
            # 변경 사항이 있는 경우에만 저장
            if changes:
                # 임시 파일에 먼저 저장
                temp_path = f"{config_path}.temp"
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(updated_config)
                
                # 변경 이력 기록
                history[coin_ticker].append({
                    'timestamp': timestamp,
                    'changes': changes,
                    'backup_path': backup_path
                })
                self.save_parameter_history(history)
                
                # 실제 파일 업데이트
                os.replace(temp_path, config_path)
                
                log.log('TR', f"{coin_ticker} 설정이 업데이트되었습니다. 변경사항: {changes}")
                return True
            
            return False
            
        except Exception as e:
            log.log('WA', f"{coin_ticker} 설정 업데이트 중 오류: {str(e)}")
            self.rollback_config(coin_ticker)
            return False

    def rollback_config(self, coin_ticker):
        """설정 롤백"""
        try:
            history = self.load_parameter_history()
            if coin_ticker in history and history[coin_ticker]:
                last_change = history[coin_ticker][-1]
                backup_path = last_change['backup_path']
                config_path = f'config/coins/{coin_ticker.lower()}_config.py'
                
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, config_path)
                    log.log('TR', f"{coin_ticker} 설정이 이전 버전으로 롤백되었습니다.")
                    return True
            return False
        except Exception as e:
            log.log('WA', f"{coin_ticker} 설정 롤백 중 오류: {str(e)}")
            return False

    def load_parameter_history(self):
        """파라미터 변경 이력 로드"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_parameter_history(self, history):
        """파라미터 변경 이력 저장"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            log.log('WA', f"파라미터 변경 이력 저장 중 오류: {str(e)}")

    def get_current_parameters(self, coin_ticker):
        """현재 파라미터 값 조회"""
        try:
            config_path = f'config/coins/{coin_ticker.lower()}_config.py'
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            params = {}
            for param in self.max_adjustment_rates.keys():
                match = re.search(f"{param}\s*=\s*([0-9.]+)", content)
                if match:
                    params[param] = float(match.group(1))
            return params
        except Exception as e:
            log.log('WA', f"{coin_ticker} 현재 파라미터 조회 중 오류: {str(e)}")
            return {}

    def apply_analysis_results(self):
        """분석 결과를 설정에 적용 (안전장치 포함)"""
        try:
            if not Config.AUTO_ADJUST_PARAMS:
                log.log('TR', "자동 파라미터 조정이 비활성화되어 있습니다.")
                return False
            
            reports = self.create_report()
            if not reports:
                return False
            
            success = True
            for coin_ticker, report in reports.items():
                if 'suggestions' in report:
                    if self.update_coin_config(coin_ticker, report['suggestions']):
                        # 파라미터 조정 알림 추가
                        adjust_msg = (
                            f"🔄 {coin_ticker} 파라미터 자동 조정\n"
                            "변경된 파라미터:\n"
                        )
                        for param, value in report['suggestions'].items():
                            adjust_msg += f"{param}: {value:.4f}\n"
                        send_telegram_alert(adjust_msg, Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)
                    else:
                        success = False
                    
            return success
            
        except Exception as e:
            log.log('WA', f"분석 결과 적용 중 오류: {str(e)}")
            return False

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
                    price_match = re.search(r'매수가: ([\d,]+)원', message)
                    if price_match:
                        trade_info['price'] = float(price_match.group(1).replace(',', ''))
                    # 수량 추출
                    amount_match = re.search(r'매수량: ([\d.]+)', message)
                    if amount_match:
                        trade_info['amount'] = float(amount_match.group(1))
                    
                # 매도 기록
                elif '매도' in message:
                    trade_info['type'] = 'SELL'
                    # 가격 추출
                    price_match = re.search(r'매도가: ([\d,]+)원', message)
                    if price_match:
                        trade_info['price'] = float(price_match.group(1).replace(',', ''))
                    # 수량 추출
                    amount_match = re.search(r'매도량: ([\d.]+)', message)
                    if amount_match:
                        trade_info['amount'] = float(amount_match.group(1))
                    # 수익률 추출
                    profit_match = re.search(r'거수익: ([+-]?\d+\.?\d*)%', message)
                    if profit_match:
                        trade_info['profit'] = float(profit_match.group(1))
                
                if trade_info['price'] is not None and trade_info['amount'] is not None:
                    return trade_info
                
            return None
            
        except Exception as e:
            log.log('WA', f"로그 파싱 중 오류: {str(e)}")
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

    def notify_trade_execution(self, trade_info):
        """체결 시 Telegram 알림 전송"""
        # 매수/매도 구분
        if 'type' in trade_info:
            if trade_info['type'] == 'BUY':
                emoji = "💵"  # 매수는 현금 이모지
                action = "매수"
            else:  # SELL
                emoji = "💰"  # 매도는 돈주머니 이모지
                action = "매도"
        else:
            emoji = "💱"  # 기본 거래 이모지
            action = "체결"

        # 수익률 표시 (매도의 경우)
        profit_text = ""
        if 'profit' in trade_info and trade_info['profit'] is not None:
            profit = trade_info['profit']
            if profit > 0:
                profit_text = f"\n수익률: ✨ +{profit:.2f}%"
            else:
                profit_text = f"\n수익률: 📉 {profit:.2f}%"

        # 메시지 구성
        message = (
            f"{emoji} {trade_info['market']} {action}\n"
            f"가격: {trade_info['price']:,.0f}원\n"
            f"수량: {trade_info['amount']:.4f}"
            f"{profit_text}"
        )
        
        send_telegram_alert(message, Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)

    def execute_trade(self, trade_info):
        """거래 실행 로직"""
        self.notify_trade_execution(trade_info)

def main():
    analyzer = TradeAnalyzer()
    
    if Config.AUTO_ADJUST_PARAMS:
        success = analyzer.apply_analysis_results()
        if success:
            log.log('TR', "파라미터 자동 조정이 완료되었습니다.")
        else:
            log.log('WA', "파라미터 자동 조정 중 문제가 발생했습니다.")
    else:
        report = analyzer.create_report()
        if report:
            print("\n=== 거래 분석 리포트 ===")
            for coin_ticker, coin_report in report.items():
                print(f"\n[{coin_ticker} 분석 결과]")
                stats = coin_report['statistics']
                print(f"총 거래 횟수: {stats['total_trades']}")
                print(f"승률: {stats['win_rate']:.2f}%")
                print(f"평균 수익률: {stats['avg_profit']:.2f}%")
                
                print("\n[파라미터 제안]")
                for param, value in coin_report['suggestions'].items():
                    print(f"{param}: {value:.4f}")

if __name__ == "__main__":
    main() 