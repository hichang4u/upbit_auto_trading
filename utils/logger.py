import os
from datetime import datetime

class Logger:
    def __init__(self):
        self.base_log_dir = 'logs'
        self.current_date = None
        self.log_file = None
        self.current_log_dir = None
        self.ensure_log_directory()
        self.update_log_file()
        
    def ensure_log_directory(self):
        """로그 디렉토리 생성"""
        if not os.path.exists(self.base_log_dir):
            os.makedirs(self.base_log_dir)
            
    def get_log_directory(self):
        """현재 날짜 기반으로 로그 디렉토리 경로 생성"""
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        
        # logs/2024/01 형식의 경로 생성
        log_dir = os.path.join(self.base_log_dir, year, month)
        
        # 디렉토리가 없으면 생성
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        return log_dir
            
    def update_log_file(self):
        """현재 날짜의 로그 파일 경로 업데이트"""
        today = datetime.now().strftime('%Y%m%d')
        
        # 날짜가 변경되었는지 확인
        if today != self.current_date:
            self.current_date = today
            self.current_log_dir = self.get_log_directory()
            self.log_file = os.path.join(self.current_log_dir, f'trading_{today}.log')
            
            # 새로운 날짜의 로그 파일 시작을 표시
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"=== {today} 거래 로그 시작 ===\n")
    
    def log(self, level, message):
        """로그 기록"""
        try:
            # 날짜가 변경되었는지 확인하고 파일 업데이트
            self.update_log_file()
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"{level:<5} | {timestamp} | {message}\n"
            
            # 콘솔 출력
            print(log_message.strip())
            
            # 파일에 기록
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
                
        except Exception as e:
            print(f"로그 기록 중 오류 발생: {str(e)}")
    
    def print_header(self, message):
        """구분선과 함께 헤더 출력"""
        self.log('INFO', '=' * 50)
        self.log('INFO', f"{message:^50}")
        self.log('INFO', '=' * 50)
    
    def print_section(self, message):
        """섹션 구분선과 함�� 메시지 출력"""
        self.log('INFO', '-' * 50)
        self.log('INFO', f"{message:^50}")
        self.log('INFO', '-' * 50)

# 전역 로거 인스턴스 생성
log = Logger()