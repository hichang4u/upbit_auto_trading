import os
import logging
from datetime import datetime

class Logger:
    def __init__(self):
        self.setup_logger()
        
    def setup_logger(self):
        """로거 설정"""
        # PythonAnywhere 경로 설정
        username = os.getenv('USER', 'default')  # PythonAnywhere 사용자명
        log_dir = f'/home/{username}/logs'
        os.makedirs(log_dir, exist_ok=True)
        
        # 로그 파일명 설정
        today = datetime.now().strftime('%Y%m%d')
        log_file = f'{log_dir}/trading_{today}.log'
        
        # 기존 핸들러 제거
        if self.logger.handlers:
            for handler in self.logger.handlers:
                self.logger.removeHandler(handler)
        
        # 파일 핸들러 (권한 설정 추가)
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷 설정
        formatter = logging.Formatter('%(levelname)s|%(asctime)s|%(message)s',
                                    '%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, level, message):
        """로그 메시지 기록"""
        if level == 'TR':  # TRADE
            self.logger.info(message)
        elif level == 'WA':  # WARNING
            self.logger.warning(message)
        elif level == 'ER':  # ERROR
            self.logger.error(message)
        else:
            self.logger.debug(message)
    
    def print_header(self, message):
        """섹션 헤더 출력"""
        line = "=" * 50
        self.log('TR', f"\n{line}\n{message}\n{line}")
    
    def print_section(self, message):
        """서브섹션 헤더 출력"""
        line = "-" * 40
        self.log('TR', f"\n{line}\n{message}\n{line}")

# 전역 로거 인스턴스 생성
log = Logger()