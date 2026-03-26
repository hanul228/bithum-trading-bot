import pybithumb
import os
import time
import csv
from collections import deque
from datetime import datetime

# 환경변수 안전확인
ACCESS_KEY = os.getenv('BITHUMB_ACCESS')
SECRET_KEY = os.getenv('BITHUMB_SECRET')

if not ACCESS_KEY or not SECRET_KEY:
    print("❌ BITHUMB_ACCESS/SECRET_KEY 환경변수 필수!")
    exit(1)

bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

print("🚀 BTC 자동매매 v4.5.1 [원화무관|CSV|3봉하락]")
print(f"키: {ACCESS_KEY[:8]}*** | BTC")
print("=" * 70)

# ===== 설정 =====
TRADE_AMOUNT_KRW = 50000      # 1회 매수 시도 금액 (원화 기준, 실제 부족해도 시도)
MARKET = "BTC"
recent_prices = deque(maxlen=10)
HOLDING = False
ENTRY_PRICE = 0
trade_count = 0
api_success = 0
total_profit = 0.0
PROFIT_LOG = 'btc_profit_v4.5.csv'

def safe_price_format(price):
    try:
        return f"{float(price):,.0f}"
    except:
        return "N/A"

def log_profit(action, price, profit_pct=0, qty=0, note=""):
    global total_profit
    try:
        now = datetime.now()
        row = [
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S'),
            action,
            safe_price_format(price),
            f"{qty:.6f}",
            f"{profit_pct:.2f}",
            safe_price_format(total_profit),
            note
        ]
        write_header = not os.path.exists(PROFIT_LOG) or os.path.getsize(PROFIT_LOG) == 0

        with open(PROFIT_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['날짜','시간','유형','가격','수량','수익률(%)','누적수익','비고'])
            writer.writerow(row)
        print(f"💾 CSV 기록: {action}")
    except Exception as e:
        print(f"⚠️ CSV 기록 오류: {e}")

def get_current_price_safe():
    global api_success
    try:
        
