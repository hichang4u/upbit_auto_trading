import os
import traceback
from datetime import datetime

class Logger:
    def __init__(self):
        self.base_log_dir = 'logs'
        self.current_date = None
        self.trade_log_file = None
        self.system_log_file = None
        self.error_log_file = None  # 오류 로그 파일 추가
        self.current_log_dir = None
        self.ensure_log_directory()
        self.update_log_files()
        
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
            
    def update_log_files(self):
        """현재 날짜의 로그 파일 경로 업데이트"""
        today = datetime.now().strftime('%Y%m%d')
        
        # 날짜가 변경되었는지 확인
        if today != self.current_date:
            self.current_date = today
            self.current_log_dir = self.get_log_directory()
            
            # 거래 로그와 시스템 로그 파일 경로 설정
            self.trade_log_file = os.path.join(self.current_log_dir, f'trade_{today}.log')
            self.system_log_file = os.path.join(self.current_log_dir, f'system_{today}.log')
            self.error_log_file = os.path.join(self.current_log_dir, f'error_{today}.log')  # 오류 로그 파일 경로
            
            # 새로운 날짜의 로그 파일 시작을 표시
            for log_file in [self.trade_log_file, self.system_log_file, self.error_log_file]:
                if not os.path.exists(log_file):
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"=== {today} 로그 시작 ===\n")
    
    def log(self, level, message, log_type='trade'):
        """로그 기록"""
        try:
            # 날짜가 변경되었는지 확인하고 파일 업데이트
            self.update_log_files()
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"{level:<5} | {timestamp} | {message}\n"
            
            # 콘솔 출력
            print(log_message.strip())
            
            # 파일에 기록
            log_file = self.system_log_file if log_type == 'system' else self.trade_log_file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
                
        except Exception as e:
            print(f"로그 기록 중 오류 발생: {str(e)}")
    
    def detailed_error(self, context, error, stack_info=True):
        """상세 오류 로깅 (스택 트레이스 포함)"""
        try:
            self.update_log_files()
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 안전하게 에러 타입과 메시지 추출
            try:
                error_type = type(error).__name__
            except:
                error_type = "UnknownErrorType"
                
            try:
                error_message = str(error)
            except:
                error_message = "Error message cannot be converted to string"
            
            # 오류 메시지 형식 생성
            lines = [
                f"ERROR | {timestamp} | {context}",
                f"Type: {error_type}",
                f"Message: {error_message}"
            ]
            
            # 스택 트레이스 추가
            if stack_info:
                lines.append("Stack Trace:")
                try:
                    stack_trace = traceback.format_exc()
                    lines.append(stack_trace)
                except:
                    lines.append("Failed to get stack trace")
            
            # 구분선 추가
            lines.append("-" * 80)
            error_log = "\n".join(lines)
            
            # 콘솔 출력
            print(error_log)
            
            # 오류 로그 파일에 기록
            with open(self.error_log_file, 'a', encoding='utf-8') as f:
                f.write(error_log + "\n")
            
            # 일반 로그에도 간단히 기록
            try:
                short_message = f"{context}: {error_type} - {error_message[:100]}"
            except:
                short_message = f"{context}: Error details not available"
                
            self.log('ERR', short_message)
            
        except Exception as e:
            print(f"오류 로깅 중 추가 오류 발생: {str(e)}")
            # 기본 로그에 간단하게 기록
            self.log('ERR', f"{context}: 상세 오류 로깅 실패")
    
    def system_log(self, level, message):
        """시스템 로그 기록"""
        self.log(level, message, log_type='system')
    
    def trade_log(self, level, message):
        """거래 로그 기록"""
        self.log(level, message, log_type='trade')
    
    def print_header(self, message, log_type='trade'):
        """구분선과 함께 헤더 출력"""
        self.log('INFO', '=' * 50, log_type)
        self.log('INFO', f"{message:^50}", log_type)
        self.log('INFO', '=' * 50, log_type)
    
    def print_section(self, message, log_type='trade'):
        """섹션 구분선과 함께 메시지 출력"""
        self.log('INFO', '-' * 50, log_type)
        self.log('INFO', f"{message:^50}", log_type)
        self.log('INFO', '-' * 50, log_type)

# 전역 로거 인스턴스 생성
log = Logger()