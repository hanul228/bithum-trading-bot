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
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

if not ACCESS_KEY or not SECRET_KEY:
    print("❌ BITHUMB_ACCESS/SECRET_KEY 환경변수 필수!")
    exit(1)

bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

print("🚀 BTC 자동매매 v4.5 [텔레그램+CSV|3봉하락|ChatID:8402630379]")
print(f"키: {ACCESS_KEY[:8]}*** | BTC | 실시간알림")
print("=" * 70)

# ===== v4.5 완전 설정 =====
TRADE_AMOUNT = 50000      # 5만원 고정
MARKET = "BTC"
recent_prices = deque(maxlen=10)
HOLDING = False
ENTRY_PRICE = 0
trade_count = 0
api_success = 0
total_profit = 0.0
PROFIT_LOG = 'btc_profit_v4.5.csv'

def safe_price_format(price):
    """가격 포맷"""
    try:
        return f"{float(price):,.0f}"
    except:
        return "N/A"

def send_telegram(msg):
    """텔레그램 전송 (ChatID:8402630379)"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 설정없음 (GitHub Secrets 확인)")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}
        requests.post(url, data=data, timeout=5)
        print("📱 텔레그램 알림 발송!")
        return True
    except Exception as e:
        print(f"⚠️ 텔레그램 오류: {e}")
        return False

def log_profit(action, price, profit_pct=0, qty=0, note=""):
    """CSV 수익 기록"""
    global total_profit
    now = datetime.now()
    row = [now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), action, 
           safe_price_format(price), f"{qty:.6f}", f"{profit_pct:.2f}", 
           safe_price_format(total_profit), note]
    
    try:
        with open(PROFIT_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(['날짜','시간','유형','가격','수량','수익률(%)','누적수익','비고'])
            writer.writerow(row)
    except:
        pass

def get_current_price_safe():
    """현재가 3중 폴백"""
    global api_success
    
    try:
        ticker = pybithumb.get_ticker(MARKET)
        if ticker:
            price = float(ticker.get('closing_price', 0))
            if price > 0:
                api_success += 1
                return price, 'ticker'
    except: pass
    
    try:
        price = bithumb.get_current_price(MARKET)
        if price:
            api_success += 1
            return float(price), 'current'
    except: pass
    
    try:
        if recent_prices:
            api_success += 1
            return float(list(recent_prices)[-1]), 'reuse'
    except: pass
    
    return None, None

def simple_entry_signal(price):
    """3중 단순 진입 신호"""
    if len(recent_prices) < 5:
        return False, "⏳ 데이터부족"
    
    prices = list(recent_prices)[-5:]
    
    consecutive_down = (
        prices[-1] < prices[-2] and 
        prices[-2] < prices[-3] and 
        prices[-3] < prices[-4]
    )
    
    avg_5 = sum(prices) / 5
    below_avg = price <= avg_5 * 0.99
    
    if consecutive_down and below_avg:
        return True, f"✅ 3하락+평균{((avg_5-price)/avg_5)*100:.1f}%↓"
    
    return False, "➡️ 대기중"

def get_balance_btc_safe():
    """BTC 잔고"""
    try:
        balance = bithumb.get_balance(MARKET)
        if isinstance(balance, tuple) and len(balance) >= 2:
            return float(balance[0]) + float(balance[1])
        return 0.0
    except:
        return 0.0

def get_krw_balance_safe():
    """원화 잔고"""
    try:
        balance = bithumb.get_balance(MARKET)
        if isinstance(balance, tuple) and len(balance) >= 4:
            return float(balance[2])
        return 0.0
    except:
        return 0.0

# 🚀 v4.5 시작 + 첫 알림!
print("🎯 v4.5 텔레그램+CSV 완전 버전 시작!")
send_telegram("🚀 <b>BTC v4.5 시작!</b>\n⏰ 실시간 모니터링\n📊 ChatID:8402630379 연결됨")
print("=" * 70)

while True:
    try:
        price, source = get_current_price_safe()
        if not price:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ 가격수집실패 → 30초 대기")
            time.sleep(30)
            continue
        
        recent_prices.append(price)
        
        print(f"[{time.strftime('%H:%M:%S')}] {safe_price_format(price)} | "
              f"데이터:{len(recent_prices)}개 | BTC:{get_balance_btc_safe():.6f} | "
              f"원화:{safe_price_format(get_krw_balance_safe())} | API:{api_success}회 | {source}")
        
        if len(recent_prices) >= 5:
            signal_ok, signal_msg = simple_entry_signal(price)
            print(f"🎯 신호: {signal_msg}")
            
            # 🟢 매수 조건
            if signal_ok and not HOLDING:
                krw_balance = get_krw_balance_safe()
                if krw_balance < TRADE_AMOUNT * 1.01:
                    print(f"❌ 원화 부족: {safe_price_format(krw_balance)}")
                else:
                    print(f"🟢 [v4.5매수] 50,000원 | {signal_msg}")
                    order = bithumb.buy_market_order(MARKET, TRADE_AMOUNT)
                    print(f"✅ 매수결과: {order}")
                    trade_count += 1
                    
                    if isinstance(order, dict) and order.get('status') == '0000':
                        HOLDING = True
                        ENTRY_PRICE = price
                        qty = TRADE_AMOUNT / price
                        log_profit('매수', price, qty=qty, note=signal_msg)
                        
                        msg = f"""🚀 <b>BTC v4.5 매수!</b>
⏰ {datetime.now().strftime('%H:%M:%S')}
💰 {safe_price_format(price)}원
📈 {signal_msg}
📊 총거래: {trade_count}회"""
                        send_telegram(msg)
                    else:
                        print(f"⚠️ 매수실패: {order}")
            
            # 🔴 매도 조건
            elif HOLDING and ENTRY_PRICE > 0 and price >= ENTRY_PRICE * 1.02:
                profit_pct = (price - ENTRY_PRICE) / ENTRY_PRICE * 100
                profit_krw = TRADE_AMOUNT * profit_pct / 100
                total_profit += profit_krw
                
                print(f"🔴 [v4.5매도] +{profit_pct:.1f}% | +{safe_price_format(profit_krw)}원")
                
                btc_balance = get_balance_btc_safe()
                if btc_balance > 0.00001:
                    order = bithumb.sell_market_order(MARKET, btc_balance)
                    print(f"✅ 매도결과: {order}")
                    
                    if isinstance(order, dict) and order.get('status') == '0000':
                        HOLDING = False
                        ENTRY_PRICE = 0
                        log_profit('매도', price, profit_pct, qty=btc_balance, note=f"+{profit_krw:,.0f}원")
                        
                        msg = f"""🔴 <b>BTC v4.5 매도!</b>
⏰ {datetime.now().strftime('%H:%M:%S')}
💰 {safe_price_format(price)}원 <b>(+{profit_pct:.1f}%)</b>
💵 수익: <b>+{safe_price_format(profit_krw)}원</b>
📊 총거래: {trade_count}회 | 누적: <b>{safe_price_format(total_profit)}</b>"""
                        send_telegram(msg)
        
        status = "🟢보유중" if HOLDING else "⚪대기중"
        profit_info = f" | +{((price-ENTRY_PRICE)/ENTRY_PRICE*100):.1f}%" if HOLDING and ENTRY_PRICE > 0 else ""
        print(f"상태: {status}{profit_info} | 진입가: {safe_price_format(ENTRY_PRICE) if HOLDING else '없음'}")
        print("=" * 70)
        
        # 1시간 요약
        if api_success % 240 == 0 and api_success > 0:
            summary = f"""📈 <b>v4.5 1시간 요약</b>
⏰ {datetime.now().strftime('%H:%M:%S')}
📊 총거래: {trade_count}회
💰 누적수익: {safe_price_format(total_profit)}원"""
            send_telegram(summary)
        
        time.sleep(15)
        
    except KeyboardInterrupt:
        print("\n⏹️ 중지됨 (Ctrl+C)")
        break
    except Exception as e:
        print(f"❌ 오류: {e}")
        time.sleep(15)
