import jwt
import hashlib
import os
import requests
import uuid
from urllib.parse import urlencode, unquote
from dotenv import load_dotenv

def get_account_info():
    # .env 파일 로드
    load_dotenv()

    # 환경 변수에서 API 키 가져오기
    UPBIT_ACCESS = os.getenv('UPBIT_ACCESS_KEY')
    UPBIT_SECRET = os.getenv('UPBIT_SECRET_KEY')

    server_url = 'https://api.upbit.com'

    # JWT 토큰 생성
    payload = {
        'access_key': UPBIT_ACCESS,
        'nonce': str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, UPBIT_SECRET, algorithm='HS256')
    authorization = 'Bearer {}'.format(jwt_token)
    headers = {
      'Authorization': authorization,
    }

    # 전체 계좌 조회 요청
    res = requests.get(server_url + '/v1/accounts', headers=headers)
    data = res.json()

    # 계좌 정보 출력
    for row in data:
        currency = row.get('currency')
        balance  = row.get('balance')
        locked   = row.get('locked')
        
        if float(balance) == 0:
            print(currency, locked)

        elif float(balance) > 0.0001:
            print(currency, balance)

if __name__ == "__main__":
    get_account_info() 