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

print("🚀 BTC 자동매매 v4.5.1 [긴급패치|CSV|3봉하락]")
print(f"키: {ACCESS_KEY[:8]}*** | BTC")
print("=" * 70)

# ===== v4.5.1 설정 =====
TRADE_AMOUNT = 50000
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
        ticker = pybithumb.get_ticker(MARKET)
        if ticker and ticker.get('closing_price'):
            price = float(ticker['closing_price'])
            if price > 10_000_000:  # 비정상 가격 필터
                api_success += 1
                return price, 'ticker'
    except:
        pass
    
    try:
        price = bithumb.get_current_price(MARKET)
        if price and price > 10_000_000:
            api_success += 1
            return float(price), 'current'
    except:
        pass
    
    if recent_prices:
        api_success += 1
        return float(list(recent_prices)[-1]), 'reuse'
    
    return None, None

def simple_entry_signal(price):
    if len(recent_prices) < 5:
        return False, f"⏳ 데이터 {len(recent_prices)}/5"
    
    prices = list(recent_prices)[-5:]
    consecutive_down = (
        prices[-1] < prices[-2] and 
        prices[-2] < prices[-3] and 
        prices[-3] < prices[-4]
    )
    
    avg_5 = sum(prices) / 5
    below_avg = price <= avg_5 * 0.99
    
    if consecutive_down and below_avg:
        drop_pct = (avg_5 - price) / avg_5 * 100
        return True, f"✅ 3하락+{drop_pct:.1f}%↓"
    return False, "➡️ 대기중"

def get_balance_safe(currency="KRW"):
    """원화/KRW/BTC 잔고 조회"""
    try:
        balance = bithumb.get_balance(MARKET if currency=="BTC" else "KRW")
        if isinstance(balance, (list, tuple)):
            if currency == "KRW":
                # [0]=보유원, [1]=사용중 원, [2]=총 원
                return float(balance[2]) if len(balance) > 2 else 0.0
            elif currency == "BTC":
                # [0]=보유 코인, [1]=주문 중 코인
                return float(balance[0]) + float(balance[1]) if len(balance) > 1 else 0.0
        elif isinstance(balance, dict):
            return float(balance.get('total_' + currency.lower(), 0))
        return 0.0
    except:
        return 0.0

# 🚀 v4.5.1 시작!
print("🎯 v4.5.1 긴급패치 버전 시작! (원화+CSV 수정)")
print("=" * 70)

while True:
    try:
        price, source = get_current_price_safe()
        if not price:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ 가격실패 → 30초 대기")
            time.sleep(30)
            continue
        
        recent_prices.append(price)
        krw_balance = get_balance_safe("KRW")
        btc_balance = get_balance_safe("BTC")
        
        print(
            f"[{time.strftime('%H:%M:%S')}] {safe_price_format(price)} | "
            f"데이터:{len(recent_prices)}개 | BTC:{btc_balance:.6f} | "
            f"원화:{safe_price_format(krw_balance)} | API:{api_success}회 | {source}"
        )
        
        if len(recent_prices) >= 5:
            signal_ok, signal_msg = simple_entry_signal(price)
            print(f"🎯 신호: {signal_msg}")
            
            # 🟢 매수
            if signal_ok and not HOLDING and krw_balance >= TRADE_AMOUNT * 1.01:
                print(f"🟢 [v4.5.1매수] 50,000원 | {signal_msg}")
                order = bithumb.buy_market_order(MARKET, TRADE_AMOUNT)
                print(f"✅ 매수결과: {order}")
                trade_count += 1
                
                if isinstance(order, dict) and order.get('status') == '0000':
                    HOLDING = True
                    ENTRY_PRICE = price
                    qty = TRADE_AMOUNT / price
                    log_profit('매수', price, qty=qty, note=signal_msg)
                else:
                    print(f"⚠️ 매수실패: {order}")
            elif signal_ok and not HOLDING:
                print(f"❌ 원화 부족: {safe_price_format(krw_balance)}")
            
            # 🔴 매도
            elif HOLDING and ENTRY_PRICE > 0 and price >= ENTRY_PRICE * 1.02:
                profit_pct = (price - ENTRY_PRICE) / ENTRY_PRICE * 100
                profit_krw = TRADE_AMOUNT * profit_pct / 100
                total_profit += profit_krw
                
                print(f"🔴 [v4.5.1매도] +{profit_pct:.1f}% | +{safe_price_format(profit_krw)}")
                
                btc_balance = get_balance_safe("BTC")
                if btc_balance > 0.00001:
                    order = bithumb.sell_market_order(MARKET, btc_balance)
                    print(f"✅ 매도결과: {order}")
                    
                    if isinstance(order, dict) and order.get('status') == '0000':
                        HOLDING = False
                        ENTRY_PRICE = 0
                        log_profit('매도', price, profit_pct, qty=btc_balance, note=f"+{profit_krw:,.0f}원")
                    else:
                        print(f"⚠️ 매도실패: {order}")
        
        status = "🟢보유중" if HOLDING else "⚪대기중"
        profit_info = (
            f" | +{((price-ENTRY_PRICE)/ENTRY_PRICE*100):.1f}%"
            if HOLDING and ENTRY_PRICE > 0 else ""
        )
        print(f"상태: {status}{profit_info} | 진입가: {safe_price_format(ENTRY_PRICE) if HOLDING else '없음'}")
        print("=" * 70)
        
        time.sleep(15)
        
    except KeyboardInterrupt:
        print("\n⏹️ 중지됨")
        break
    except Exception as e:
        print(f"❌ 오류: {e}")
        time.sleep(15)
