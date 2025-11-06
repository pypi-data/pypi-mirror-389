import logging

SUCCESS_LEVEL = 25
FAIL_LEVEL = 35
CRITICAL_LEVEL = 45

logging.addLevelName(SUCCESS_LEVEL, 'SUCCESS')
logging.addLevelName(FAIL_LEVEL, 'FAIL')
logging.addLevelName(CRITICAL_LEVEL, 'CRITICAL')