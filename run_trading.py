#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# 로그 디렉토리 설정
username = os.getenv('USER', 'default')
log_dir = os.getenv('LOG_DIR', f'/home/{username}/logs')
os.makedirs(log_dir, exist_ok=True)

# 표준 출력/에러를 파일로 리다이렉션
log_file = f'{log_dir}/app_{datetime.now().strftime("%Y%m%d")}.log'
sys.stdout = open(log_file, 'a', encoding='utf-8', buffering=1)
sys.stderr = sys.stdout

from main import main

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error occurred at {datetime.now()}: {str(e)}")
        sys.exit(1)
    finally:
        sys.stdout.close() 