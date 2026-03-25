import pybithumb
import os
import time

ACCESS_KEY = os.getenv('BITHUMB_ACCESS')
SECRET_KEY = os.getenv('BITHUMB_SECRET')
bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

print("🧪 BTC 테스트 매매 봇 시작!")
print(f"키 로드: {ACCESS_KEY[:8]}...")

while True:
    try:
        # 1. 잔고 확인 (실제 데이터)
        balance = bithumb.get_balance("BTC")
        total_krw = float(balance['data']['total_account'])
        btc_balance = float(balance['data']['BTC'])
        
        print(f"💰 원화: {total_krw:,.0f}원")
        print(f"₿ BTC: {btc_balance:.6f}")
        print("-" * 40)
        
        # 2. 테스트 매수 주문 (실제 주문 X)
        test_buy_price = pybithumb.get_current_price("BTC") * 0.98
        test_buy_amount = total_krw * 0.01  # 1% 테스트
        
        print(f"🟢 테스트 매수: {test_buy_amount:,.0f}원 ({test_buy_price:,.0f}원)")
        
        # 3. 테스트 매도 주문  
        test_sell_price = pybithumb.get_current_price("BTC") * 1.02
        print(f"🔴 테스트 매도: {btc_balance:.6f}BTC ({test_sell_price:,.0f}원)")
        
        print("=" * 50)
        
        time.sleep(30)  # 30초 대기
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        time.sleep(30)
