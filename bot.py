import pybithumb
import os
import time
import csv
import requests
from collections import deque
from datetime import datetime

# 환경변수 안전확인
ACCESS_KEY = os.getenv('BITHUMB_ACCESS')
SECRET_KEY = os.getenv('BITHUMB_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '8402630379')

if not ACCESS_KEY or not SECRET_KEY:
    print("❌ BITHUMB_ACCESS/SECRET_KEY 환경변수 필수!")
    exit(1)

bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

# ===== 설정 =====
TRADE_AMOUNT = 50000
MARKET = "BTC"
recent_prices =
