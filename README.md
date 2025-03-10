# 업비트 자동 거래 시스템 (Upbit Auto Trading)

업비트 암호화폐 거래소를 이용한 자동 거래 시스템입니다. RSI, 볼린저 밴드, 거래량 지표를 활용한 매매 전략으로 암호화폐(XRP) 자동 거래를 수행합니다.

## 주요 기능

- 설정 가능한 매매 전략 (RSI, 볼린저 밴드, 거래량 기반)
- 실제 거래 및 시뮬레이션 모드 지원
- 일일 거래 분석 및 보고서 생성
- 텔레그램 알림 기능
- Windows 서비스 형태로 백그라운드 실행 가능

## 필수 요구사항

- Python 3.8 이상
- 업비트 API 키
- Windows 환경 (서비스 모드 실행 시)

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/upbit_auto_trading.git
cd upbit_auto_trading
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
venv\Scripts\activate
```

3. 필요 패키지 설치
```bash
pip install -r requirements.txt
```

## 설정 방법

### 1. 환경 변수 설정 (.env 파일)

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 정보를 입력합니다:

```
UPBIT_ACCESS_KEY=업비트_액세스_키
UPBIT_SECRET_KEY=업비트_시크릿_키
TELEGRAM_BOT_TOKEN=텔레그램_봇_토큰
TELEGRAM_CHAT_ID=텔레그램_채팅_ID
USER=사용자_이름
LOG_DIR=로그_디렉토리_경로
```

### 2. 매매 전략 설정

매매 전략은 다음과 같이 설정되어 있습니다:

- **매수 조건**: 
  - RSI ≤ 25 (과매도 상태)
  - 현재가가 볼린저 밴드 하단 이하
  - 거래량 증가 추세

- **매도 조건**:
  - RSI ≥ 75 (과매수 상태)
  - 현재가가 볼린저 밴드 상단 이상
  - 거래량 증가 추세

`config` 디렉토리의 파일을 수정하여 전략 파라미터를 변경할 수 있습니다.

## 실행 방법

### 일반 실행

```bash
python main.py
```

### 전략 확인

현재 시장 상황에서 매매 전략 상태를 확인하려면:

```bash
python check_strategy.py
```

### 서비스 모드 (Windows)

Windows 환경에서 백그라운드 서비스로 실행할 수 있습니다.

#### 서비스 설치
```
install_service.bat
```

#### 서비스 시작
```
net start UpbitAutoTrader
```
또는
```
start_service.bat
```
또는 서비스 관리자(services.msc)에서 "Upbit Auto Trader" 서비스 시작

#### 서비스 중지
```
net stop UpbitAutoTrader
```
또는
```
stop_service.bat
```

#### 서비스 제거
```
remove_service.bat
```

## 로그 확인

거래 로그는 기본적으로 `logs` 디렉토리에 저장됩니다. 환경 변수 `LOG_DIR`을 설정하여 로그 저장 위치를 변경할 수 있습니다.

## 주의 사항

- 이 시스템은 투자 손실을 보장하지 않습니다. 실제 거래 전 충분한 테스트를 권장합니다.
- 시뮬레이션 모드에서 충분히 테스트한 후 실제 거래를 진행하세요.
- API 키는 안전하게 보관하고, 필요한 권한만 부여하세요.

## 라이선스

이 프로젝트는 MIT 라이선스에 따라 배포됩니다. 