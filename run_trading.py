#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from utils.logger import log

if __name__ == "__main__":
    try:
        log.system_log('INFO', f"System started at {datetime.now()}")
        from main import main
        main()
    except Exception as e:
        log.system_log('ERROR', f"Error occurred at {datetime.now()}: {str(e)}")
        sys.exit(1)
    finally:
        log.system_log('INFO', f"System stopped at {datetime.now()}") 