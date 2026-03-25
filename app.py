import pybithumb
import os
import time
from collections import deque

# 환경변수 안전확인
ACCESS_KEY = os.getenv('BITHUMB_ACCESS')
SECRET_KEY = os.getenv('BITHUMB_SECRET')

if not ACCESS_KEY or not SECRET_KEY:
    print("❌ BITHUMB_ACCESS/SECRET_KEY 환경변수 필수!")
    exit(1)

bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

print("💎 BTC 자동매매 v3.0 [네코드+실시간ticker+동적전략]")
print(f"키: {ACCESS_KEY[:8]}*** | pybithumb BTC | 24/7")

TRADE_AMOUNT = 40000
MARKET = "BTC"  # ✅ pybithumb 표준 (네코드 승리!)
candles_10min = deque(maxlen=40)
HOLDING = False
LAST_PRICE = 0
trade_count = 0

def safe_price_format(price):
    """완벽한 가격 출력 (None방지)"""
    try:
        return f"{float(price):,.0f}"
    except:
        return "N/A"

def get_ticker_data():
    """✅ 네 코드 핵심! 실제 ticker → OHLCV 변환"""
    try:
        ticker = pybithumb.get_ticker(MARKET) or {}
        price = float(ticker.get('closing_price', 0))
        volume_24h = float(ticker.get('acc_trade_volume_24H', 0))
        volume_10m = volume_24h / 144  # 24시간→10분 평균 (네 로직!)
        
        if price > 0:
            return {
                'open': price * 0.9995,    # ✅ 현실적 OHLC (네 방식)
                'high': price * 1.0015,
                'low': price * 0.9985,
                'close': price,
                'volume': max(volume_10m, price * 0.0005)  # 최소 거래량 보장
            }
    except:
        pass
    return None

def get_balance_btc_safe():
    """✅ 튜플/딕셔너리 모두 처리 (네 방식)"""
    try:
        balance = bithumb.get_balance(MARKET)
        if isinstance(balance, tuple) and len(balance) >= 2:
            return float(balance[0]) + float(balance[1])
        elif isinstance(balance, dict) and 'data' in balance:
            return float(balance['data'].get(MARKET, 0))
        return 0.0
    except:
        return 0.0

def analyze_market_safe():
    """✅ 네 분석로직 + 내 안전장치"""
    if len(candles_10min) < 20:
        return 0.025, 0.045, "⏳ 데이터수집중"
    
    recent = list(candles_10min)[-10:]
    prior = list(candles_10min)[-20:-10]
    
    try:
        # 가격 추세 (네 로직)
        prior_avg = sum(c['close'] for c in prior) / 10
        recent_avg = sum(c['close'] for c in recent) / 10
        price_trend = (recent_avg - prior_avg) / prior_avg if prior_avg else 0
        
        # 거래량 추세 (네 로직)
        prior_vol = sum(c['volume'] for c in prior) / 10
        recent_vol = sum(c['volume'] for c in recent) / 10
        vol_trend = (recent_vol / prior_vol - 1) if prior_vol else 0
        
        base_buy, base_sell = 0.025, 0.045
        
        # ✅ 네 3단계 판단로직 그대로!
        if vol_trend > 0.3:
            momentum = "🔥 거래량폭발"
            buy_drop, sell_rise = base_buy*0.85, base_sell*1.1
        elif price_trend * vol_trend > 0.02:
            momentum = "🚀 모멘텀강함"
            buy_drop, sell_rise = base_buy*0.9, base_sell*1.15
        else:
            momentum = "➡️ 안정추세"
            buy_drop, sell_rise = base_buy, base_sell
            
        return (max(0.015, min(0.035, buy_drop)), 
                max(0.04, min(0.06, sell_rise)), momentum)
    except:
        return 0.025, 0.045, "❓ 계산오류"

print("🔄 5분 데이터수집 → 20분 자동매매 시작")
print("=" * 70)

while True:
    try:
        # ✅ 네 핵심! ticker 데이터 활용
        candle = get_ticker_data()
        if candle:
            candles_10min.append(candle)
            price = candle['close']
        else:
            price = pybithumb.get_current_price(MARKET)
            if not price:
                print("⚠️ 가격데이터 없음 → 대기")
                time.sleep(15)
                continue
        
        # 안전 출력
        print(f"[{time.strftime('%H:%M:%S')}] {safe_price_format(price)} | "
              f"데이터:{len(candles_10min)}개 | BTC:{get_balance_btc_safe():.6f}")
        
        # 기준가 설정
        if LAST_PRICE == 0 and len(candles_10min) >= 5:
            LAST_PRICE = price
            print(f"📊 기준가: {safe_price_format(LAST_PRICE)}")
        
        # 자동매매 (20개 데이터 확보)
        if len(candles_10min) >= 20 and LAST_PRICE > 0:
            buy_drop, sell_rise, momentum = analyze_market_safe()
            print(f"🎯 {momentum} | 매수:{buy_drop*100:.1f}%↓ | "
                  f"매도:{sell_rise*100:.1f}%↑")
            
            # 매수
            if not HOLDING and price <= LAST_PRICE * (1 - buy_drop):
                print("🟢 [매수실행]")
                order = bithumb.buy_market_order(MARKET, TRADE_AMOUNT)
                print(f"✅ 매수: {order}")
                trade_count += 1
                if isinstance(order, dict) and order.get('status') == '0000':
                    HOLDING = True
                LAST_PRICE = price
            
            # 매도
            elif HOLDING and price >= LAST_PRICE * (1 + sell_rise):
                print("🔴 [매도실행]")
                btc_balance = get_balance_btc_safe()
                if btc_balance > 0.00001:
                    order = bithumb.sell_market_order(MARKET, btc_balance)
                    print(f"✅ 매도: {order} (총:{trade_count}회)")
                    if isinstance(order, dict) and order.get('status') == '0000':
                        HOLDING = False
                LAST_PRICE = price
        
        status = "🟢보유중" if HOLDING else "⚪대기중"
        print(f"상태: {status} | 기준가: {safe_price_format(LAST_PRICE)}")
        print("=" * 70)
        
        time.sleep(15)
        
    except KeyboardInterrupt:
        print("\n⏹️ 중지 (Ctrl+C)")
        break
    except Exception as e:
        print(f"❌ {e}")
        time.sleep(15)
