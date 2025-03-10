from src.strategies.xrp_strategy import XRPStrategy
from config.coins.xrp_config import XRPConfig
from utils.logger import log
import traceback
from src.api_client import UpbitClient
import numpy as np
from datetime import datetime

def check_account_balance(client, coin_ticker="XRP"):
    """계좌 잔고 확인 기능"""
    print("\n" + "="*60)
    print("                 계좌 잔고 정보")
    print("="*60)
    
    try:
        # KRW 잔고 조회
        try:
            krw_balance = client.get_balance("KRW")
            print(f"💰 원화(KRW) 잔고: {krw_balance:,.0f}원")
            
            # 잔고가 0인 경우 확인 메시지
            if krw_balance == 0:
                print("⚠️ 원화 잔고가 0원입니다. 충전이 필요하거나 API 설정을 확인하세요.")
                print("- API 키가 조회 권한을 가지고 있는지 확인하세요.")
                print("- 업비트 계정에 원화가 입금되었는지 확인하세요.")
        except Exception as e:
            print(f"❌ 원화 잔고 조회 실패: {str(e)}")
            if hasattr(log, 'detailed_error'):
                log.detailed_error("원화 잔고 조회 실패", e)
        
        # 코인 잔고 조회
        try:
            coin_balance = client.get_balance(coin_ticker)
            print(f"🪙 {coin_ticker} 잔고: {coin_balance:.8f} {coin_ticker}")
            
            # 코인 평가 금액 계산
            current_price = client.get_current_price(f"KRW-{coin_ticker}")
            if current_price and coin_balance > 0:
                coin_value = current_price * coin_balance
                print(f"   평가금액: {coin_value:,.0f}원 (현재가: {current_price:,.0f}원)")
                
                # 평균 매수가 조회
                avg_buy_price = client.get_avg_buy_price(coin_ticker)
                if avg_buy_price > 0:
                    profit_rate = ((current_price - avg_buy_price) / avg_buy_price) * 100
                    profit_amount = coin_balance * avg_buy_price * (profit_rate / 100)
                    print(f"   평균단가: {avg_buy_price:,.0f}원")
                    print(f"   평가손익: {profit_amount:,.0f}원 ({profit_rate:+.2f}%)")
        except Exception as e:
            print(f"❌ {coin_ticker} 잔고 조회 실패: {str(e)}")
            if hasattr(log, 'detailed_error'):
                log.detailed_error(f"{coin_ticker} 잔고 조회 실패", e)
        
        # 전체 자산 가치 계산
        try:
            total_balance = krw_balance
            if current_price and coin_balance > 0:
                total_balance += (current_price * coin_balance)
            print(f"\n💵 총 자산 가치: {total_balance:,.0f}원")
        except Exception as e:
            print(f"❌ 총 자산 계산 실패: {str(e)}")
        
        # 전체 잔고 조회 시도 (참고용)
        try:
            all_balances = client.get_balance("all")
            if all_balances:
                print("\n📊 전체 보유 자산 목록:")
                has_assets = False
                for currency, balance_info in all_balances.items():
                    # 실제 잔고가 있는 화폐만 표시
                    if isinstance(balance_info, dict):
                        balance = float(balance_info.get('balance', 0))
                        if balance > 0:
                            has_assets = True
                            print(f"   • {currency}: {balance:.8f}")
                    elif isinstance(balance_info, (int, float, str)):
                        balance = float(balance_info)
                        if balance > 0:
                            has_assets = True
                            print(f"   • {currency}: {balance:.8f}")
                
                if not has_assets:
                    print("   보유 중인 자산이 없습니다.")
        except Exception as e:
            print(f"전체 잔고 조회 실패 (참고용): {str(e)}")
            if hasattr(log, 'detailed_error'):
                log.detailed_error("전체 잔고 조회 실패", e)
    
    except Exception as e:
        print(f"❌ 계좌 잔고 조회 중 오류 발생: {str(e)}")
        print(traceback.format_exc())

def main():
    print("\n" + "="*60)
    print("         XRP 매매 신호 분석 (RSI + 볼린저 밴드 + 거래량 전략)")
    print("="*60)
    print(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # XRP 전략 인스턴스 생성
        strategy = XRPStrategy()
        
        # API 클라이언트 설정
        client = UpbitClient()
        strategy.set_client(client)
        
        # 계좌 잔고 확인
        check_account_balance(client, "XRP")
        
        # 마켓 설정
        market = XRPConfig.MARKET  # 보통 "KRW-XRP"
        print(f"\n대상 마켓: {market}")
        
        # 현재가 조회
        current_price = strategy.get_current_price(market)
        if current_price:
            print(f"현재 XRP 가격: {current_price:,}원")
        
        # OHLCV 데이터 확인
        print("\n[일봉 데이터 조회 중...]")
        df = strategy.get_ohlcv(market)
        if df is None or df.empty:
            print("OHLCV 데이터를 가져올 수 없습니다.")
            return
        
        print(f"데이터 확인: {len(df)}일치 (최근: {df.index[-1]})")
        
        # 지표 계산
        print("\n[기술적 지표 계산 중...]")
        indicators = strategy.calculate_indicators(market)
        
        if indicators is not None:
            # 지표 안전하게 가져오기
            rsi = indicators.get('RSI', np.nan)
            bb_upper = indicators.get('BB_UPPER', np.nan)
            bb_mid = indicators.get('BB_MID', np.nan)
            bb_lower = indicators.get('BB_LOWER', np.nan)
            vol_change = indicators.get('VOL_CHANGE', np.nan)
            vol_ratio = indicators.get('VOL_RATIO', np.nan)
            
            # 결측값 확인 및 처리
            if np.isnan(rsi) or np.isnan(bb_upper) or np.isnan(bb_lower) or np.isnan(vol_change):
                print("⚠️ 일부 지표가 계산되지 않았습니다. 확인이 필요합니다.")
            
            # 안전한 조건 검사
            rsi_buy_condition = False if np.isnan(rsi) else rsi <= 25
            rsi_sell_condition = False if np.isnan(rsi) else rsi >= 75
            bb_lower_condition = False if np.isnan(bb_lower) else current_price <= bb_lower
            bb_upper_condition = False if np.isnan(bb_upper) else current_price >= bb_upper
            volume_increase_condition = False if np.isnan(vol_change) else vol_change > 0
            
            print("\n" + "-"*60)
            print("                   현재 전략 상태")
            print("-"*60)
            
            # 1. RSI 상태
            print(f"1️⃣ RSI: {rsi:.2f}")
            print(f"  • 매수 조건(RSI ≤ 25): {'✅ 충족' if rsi_buy_condition else '❌ 미충족'}")
            print(f"  • 매도 조건(RSI ≥ 75): {'✅ 충족' if rsi_sell_condition else '❌ 미충족'}")
            
            # 2. 볼린저 밴드 상태
            print(f"\n2️⃣ 볼린저 밴드:")
            print(f"  • 상단(매도선): {bb_upper:,.2f}원")
            print(f"  • 중앙선: {bb_mid:,.2f}원")
            print(f"  • 하단(매수선): {bb_lower:,.2f}원")
            print(f"  • 현재가: {current_price:,.2f}원 ({(current_price-bb_mid)/bb_mid*100:+.2f}% 중앙선 대비)")
            print(f"  • 매수 조건(현재가 ≤ 하단): {'✅ 충족' if bb_lower_condition else '❌ 미충족'}")
            print(f"  • 매도 조건(현재가 ≥ 상단): {'✅ 충족' if bb_upper_condition else '❌ 미충족'}")
            
            # 3. 거래량 상태
            print(f"\n3️⃣ 거래량:")
            if not np.isnan(vol_change):
                print(f"  • 전일 대비 변화율: {vol_change*100:+.2f}%")
            else:
                print("  • 전일 대비 변화율: 계산 불가")
                
            if not np.isnan(vol_ratio):
                print(f"  • 5일 평균 대비: {vol_ratio*100:.2f}%")
            else:
                print("  • 5일 평균 대비: 계산 불가")
                
            print(f"  • 매수/매도 조건(전일대비 증가): {'✅ 충족' if volume_increase_condition else '❌ 미충족'}")
            
            # 최종 매매 신호
            buy_signal = rsi_buy_condition and bb_lower_condition and volume_increase_condition
            sell_signal = rsi_sell_condition and bb_upper_condition and volume_increase_condition
            
            print("\n" + "="*60)
            print("                   최종 매매 신호")
            print("="*60)
            
            if buy_signal:
                print("🔵 매수 신호: ✅ 모든 조건 충족!")
                
                # 매수 시뮬레이션 정보
                krw_balance = client.get_balance("KRW")
                if krw_balance > 0:
                    trade_amount = min(krw_balance, XRPConfig.TRADE_UNIT)
                    expected_coin = trade_amount / current_price
                    print(f"\n💡 매수 시뮬레이션 (다음 주기 예상):")
                    print(f"   주문금액: {trade_amount:,.0f}원")
                    print(f"   예상수량: {expected_coin:.8f} XRP")
            else:
                print("🔵 매수 신호: ❌ 조건 미충족")
                
            if sell_signal:
                print("🔴 매도 신호: ✅ 모든 조건 충족!")
                
                # 매도 시뮬레이션 정보
                coin_balance = client.get_balance("XRP")
                if coin_balance > 0:
                    expected_krw = coin_balance * current_price
                    print(f"\n💡 매도 시뮬레이션 (다음 주기 예상):")
                    print(f"   매도수량: {coin_balance:.8f} XRP")
                    print(f"   예상금액: {expected_krw:,.0f}원")
            else:
                print("🔴 매도 신호: ❌ 조건 미충족")
                
            # 요약
            print("\n" + "-"*60)
            print("                    종합 의견")
            print("-"*60)
            
            if buy_signal:
                print("📊 현재 상황: 💰 매수 적기")
            elif sell_signal:
                print("📊 현재 상황: 💸 매도 적기")
            else:
                position = "⚖️ 중립"
                if not np.isnan(rsi):
                    if rsi < 40:
                        position = "📉 약세 (매수 대기)"
                    elif rsi > 60:
                        position = "📈 강세 (매도 대기)"
                
                print(f"📊 현재 상황: {position}")
                
                # 조건 충족까지 필요한 사항
                missing_buy = []
                if not rsi_buy_condition and not np.isnan(rsi):
                    missing_buy.append(f"RSI가 {rsi:.2f}에서 25 이하로 하락 ({rsi - 25:.2f} 차이)")
                if not bb_lower_condition and not np.isnan(bb_lower):
                    missing_buy.append(f"가격이 {current_price:,.2f}원에서 {bb_lower:,.2f}원 이하로 하락 ({current_price - bb_lower:,.2f}원 차이)")
                if not volume_increase_condition:
                    missing_buy.append("거래량 증가 (현재 감소 추세)")
                
                if missing_buy:
                    print("\n📋 매수 조건 충족까지 필요사항:")
                    for i, item in enumerate(missing_buy, 1):
                        print(f"  {i}. {item}")
        else:
            print("지표를 계산할 수 없습니다.")
    
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 