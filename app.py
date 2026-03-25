import pybithumb
import os
import time

ACCESS_KEY = os.getenv('BITHUMB_ACCESS')
SECRET_KEY = os.getenv('BITHUMB_SECRET')

print("🚀 24시간 BTC 트레이딩 봇 시작!")
print(f"키 로드: {ACCESS_KEY[:8]}...")

while True:
    try:
        price = pybithumb.get_current_price("BTC")
        print(f"[{time.strftime('%H:%M:%S')}] BTC: {price:,}원")
        time.sleep(60)
    except Exception as e:
        print(f"❌ 오류: {e}")
        time.sleep(60)
