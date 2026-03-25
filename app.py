import pybithumb
import os
import time

ACCESS_KEY = os.getenv('BITHUMB_ACCESS')
SECRET_KEY = os.getenv('BITHUMB_SECRET')
bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

print("💎 최적화 BTC 자동매매 (4만/2.5%↓→4.5%↑)")
print(f"키: {ACCESS_KEY[:8]}... | 24시간 무중단")

TRADE_AMOUNT = 40000
BUY_DROP = 0.975      # 2.5%↓
SELL_RISE = 1.045     # 4.5%↑
HOLDING = False
LAST_PRICE = 0

while True:
    try:
        price = pybithumb.get_current_price("BTC")
        print(f"[{time.strftime('%H:%M:%S')}] {price:,}")
        
        if LAST_PRICE == 0:
            LAST_PRICE = price
        
        # 매수: 2.5%↓
        if not HOLDING and price <= LAST_PRICE * BUY_DROP:
            print("🟢 2.5%↓ 매수!")
            order = bithumb.buy_market_order("BTC", TRADE_AMOUNT)
            print(f"✅ {order}")
            HOLDING = True
            LAST_PRICE = price
            
        # 매도: 4.5%↑  
        elif HOLDING and price >= LAST_PRICE * SELL_RISE:
            print("🔴 4.5%↑ 매도!")
            balance = bithumb.get_balance("BTC")
            btc = float(balance['data'].get('BTC', 0))
            order = bithumb.sell_market_order("BTC", btc)
            print(f"✅ {order}")
            HOLDING = False
            LAST_PRICE = price
            
        print(f"상태: {'🟢보유' if HOLDING else '⚪대기'} | 기준: {LAST_PRICE:,}")
        print("-"*40)
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ {e}")
        time.sleep(15)
