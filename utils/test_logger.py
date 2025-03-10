from logger import log

def test_basic_logging():
    print("=== 기본 로깅 테스트 ===")
    log.log('TR', "일반 거래 로그 테스트")
    log.log('WA', "경고 로그 테스트")
    log.system_log('INFO', "시스템 로그 테스트")
    log.print_header("헤더 테스트")
    log.print_section("섹션 테스트")
    print("기본 로깅 테스트 완료\n")

def test_error_logging():
    print("=== 오류 로깅 테스트 ===")
    
    # 일반 예외
    try:
        result = 1 / 0
    except Exception as e:
        log.detailed_error("제로 디비전 오류 테스트", e)
    
    # 문자열 변환 불가능한 예외 (예시)
    class CustomError:
        def __str__(self):
            raise ValueError("Cannot convert to string")
    
    try:
        log.detailed_error("문자열 변환 불가능 오류 테스트", CustomError())
    except Exception as e:
        print(f"문자열 변환 테스트 실패: {str(e)}")
    
    # None 전달 테스트
    log.detailed_error("None 오류 객체 테스트", None)
    
    print("오류 로깅 테스트 완료\n")

if __name__ == "__main__":
    print("로거 테스트 시작")
    test_basic_logging()
    test_error_logging()
    print("로거 테스트 완료") 