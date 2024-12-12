import os
from datetime import datetime
from utils.logger import log
from config.config import Config

def get_summary_directory():
    """현재 날짜 기반으로 요약 디렉토리 경로 생성"""
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    
    # logs/summary/2024/01 형식의 경로 생성
    summary_dir = os.path.join('logs', 'summary', year, month)
    
    # 디렉토리가 없으면 생성
    if not os.path.exists(summary_dir):
        os.makedirs(summary_dir)
        
    return summary_dir

def filter_daily_logs():
    """일일 거래 로그 필터링"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        output_dir = get_summary_directory()
        output_file = os.path.join(output_dir, f'trading_summary_{today}.log')

        # 중요 거래 관련 키워드만 필터링
        keywords = ['매수 체결', '매도 체결', '수익 실현', '손실 발생']
        levels = ['TR']  # 거래(TR) 로그만 필터링

        with open(output_file, 'w', encoding='utf-8') as out_f:
            # 헤더 추가
            out_f.write(f"=== {today} 거래 요약 ===\n\n")

            # 오늘 로그 파일 처리
            year = datetime.now().strftime('%Y')
            month = datetime.now().strftime('%m')
            log_file = os.path.join('logs', year, month, f'trading_{today}.log')
            
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if any(level in line for level in levels) and any(keyword in line for keyword in keywords):
                            out_f.write(line)
            else:
                out_f.write(f"오늘({today}) 로그 파일이 없습니다.\n")

            # 푸터 추가
            out_f.write(f"\n=== 요약 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

        log.log('TR', f"일일 거래 요약이 생성되었습니다: {output_file}")
        
    except Exception as e:
        log.log('WA', f"로그 필터링 중 오류 발생: {str(e)}")

def filter_logs_for_date(date_str):
    """특정 날짜의 로그 필터링"""
    try:
        # 날짜 문자열에서 년/월 추출
        year = date_str[:4]
        month = date_str[4:6]
        
        output_dir = os.path.join('logs', 'summary', year, month)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, f'trading_summary_{date_str}.log')

        # 중요 거래 관련 키워드만 필터링
        keywords = ['매수 체결', '매도 체결', '수익 실현', '손실 발생']
        levels = ['TR']  # 거래(TR) 로그만 필터링

        with open(output_file, 'w', encoding='utf-8') as out_f:
            out_f.write(f"=== {date_str} 거래 요약 ===\n\n")

            log_file = os.path.join('logs', year, month, f'trading_{date_str}.log')
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if any(level in line for level in levels) and any(keyword in line for keyword in keywords):
                            out_f.write(line)
            else:
                out_f.write(f"해당 날짜({date_str})의 로그 파일이 없습니다.\n")

            out_f.write(f"\n=== 요약 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

        log.log('TR', f"거래 요약이 생성되었습니다: {output_file}")
        
    except Exception as e:
        log.log('WA', f"로그 필터링 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    if Config.ENABLE_ANALYSIS:
        filter_daily_logs()
    else:
        print("자동 분석이 비활성화되어 있습니다.") 