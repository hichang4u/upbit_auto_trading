import os
import sys
import requests
from datetime import datetime

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.config import Config
from utils.logger import log

def fetch_upbit_market_info():
    """설정된 MARKET에 대한 업비트 종목 정보를 가져와 Config에 저장"""
    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        # 설정된 MARKET에 대한 정보만 필터링
        market_info = next(
            (row for row in response.json() if row.get('market') == Config.MARKET),
            None
        )

        if market_info:
            Config.UPBIT_MARKET_INFO = {
                "market": market_info.get('market'),
                "korean_name": market_info.get('korean_name')
            }
            log.log('TR', f"업비트 종목 정보가 성공적으로 업데이트되었습니다: {Config.UPBIT_MARKET_INFO}")
            return Config.UPBIT_MARKET_INFO
        else:
            log.log('WA', f"설정된 MARKET({Config.MARKET})에 대한 정보를 찾을 수 없습니다.")
            return None
            
    except requests.exceptions.RequestException as e:
        log.log('WA', f"업비트 종목 정보를 가져오는 중 오류 발생: {str(e)}")
        return None

def print_all_markets():
    """모든 업비트 마켓 정보 출력"""
    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        print("\n=== 업비트 마켓 정보 ===")
        print(f"조회 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 40)
        
        # KRW 마켓만 필터링하여 출력
        krw_markets = [row for row in response.json() if row.get('market').startswith('KRW-')]
        
        for market in krw_markets:
            print(f"{market.get('market'):<10} | {market.get('korean_name')}")
            
        print("=" * 40)
        print(f"총 {len(krw_markets)}개의 KRW 마켓이 있습니다.")
        
    except requests.exceptions.RequestException as e:
        print(f"업비트 종목 정보를 가져오는 중 오류 발생: {str(e)}")

def fetch_upbit_candles():
    """설정된 MARKET에 대한 업비트 캔들 정보를 가져와 출력"""
    url = f"https://api.upbit.com/v1/candles/minutes/30?market={Config.MARKET}&count=5"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        print("\n=== 업비트 캔들 정보 ===")
        for row in response.json():
            UTC = row.get('candle_date_time_utc')
            Open = row.get('opening_price')
            High = row.get('high_price')
            Low = row.get('low_price')
            Close = row.get('trade_price')
            
            print(f"UTC: {UTC}, Open: {Open}, High: {High}, Low: {Low}, Close: {Close}")
            
    except requests.exceptions.RequestException as e:
        print(f"업비트 캔들 정보를 가져오는 중 오류 발생: {e}")

if __name__ == "__main__":
    # 단독 실행 시 모든 마켓 정보 출력
    print_all_markets()
    
    # 설정된 MARKET 정보도 출력
    print("\n=== 설정된 마켓 정보 ===")
    market_info = fetch_upbit_market_info()
    if market_info:
        print(f"마켓: {market_info['market']}")
        print(f"한글명: {market_info['korean_name']}")
    
    # 설정된 MARKET의 캔들 정보 출력
    fetch_upbit_candles() 