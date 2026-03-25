import pybithumb
import os
import time

ACCESS_KEY = os.getenv('BITHUMB_ACCESS')
SECRET_KEY = os.getenv('BITHUMB_SECRET')
bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

print("🧪 BTC 안전 테스트 봇 시작!")
print(f"키 로드: {ACCESS_KEY[:8]}...")

while True:
    try:
        # 1. 현재가 (인증 필요 없음)
        price = pybithumb.get_current_price("BTC")
        print(f"💰 BTC 현재가: {price:,}원")
        
        # 2. 잔고 조회 (오류시 건너뛰기)
        try:
            balance = bithumb.get_balance("BTC")
            if 'data' in balance:
                total_krw = float(balance['data'].get('total_account', 0))
                btc_balance = float(balance['data'].get('BTC', 0))
                print(f"✅ 잔고 - 원화: {total_krw:,.0f}원, BTC: {btc_balance:.6f}")
            else:
                print("⚠️  잔고 조회 제한됨")
        except:
            print("⚠️  잔고 조회 스킵 (API 제한)")
        
        # 3. 테스트 매매 시뮬레이션
        test_amount = 50000  # 5만원 테스트
        test_buy_price = price * 0.98
        test_sell_price = price * 1.02
        
        print(f"🟢 테스트 매수: {test_amount:,}원 ({test_buy_price:,.0f})")
        print(f"🔴 테스트 매도: {test_amount/price:.6f}BTC ({test_sell_price:,.0f})")
        print("=" * 50)
        
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        time.sleep(30)
