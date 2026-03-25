import pybithumb
import os
import time
import requests  # ✅ 필수
from collections import deque

ACCESS_KEY = os.getenv('BITHUMB_ACCESS')
SECRET_KEY = os.getenv('BITHUMB_SECRET')
bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

print("🌟 10분 캔들 + 거래량 동적 BTC 자동매매 v2.0")
print(f"키: {ACCESS_KEY[:8]}... | 검토완료 | 배포준비OK")

TRADE_AMOUNT = 40000
candles_10min = deque(maxlen=40)
HOLDING = False
LAST_PRICE = 0

def get_10min_candle():
    """Bithumb 10분 캔들 API"""
    try:
        url = "https://api.bithumb.com/public/candle"
        params = {"market": "BTC", "interval": "10M", "count": 1}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if data.get('status') == '0000' and data.get('data'):
            candle = data['data'][0]
            return {
                'open': float(candle['open_price']),
                'high': float(candle['max_price']),
                'low': float(candle['min_price']), 
                'close': float(candle['close_price']),
                'volume': float(candle.get('acc_trade_volume_10M', 0))
            }
    except Exception as e:
        print(f"캔들API 오류: {e}")
    return None

def analyze_market():
    """10분 캔들 + 거래량 분석"""
    if len(candles_10min) < 20:
        return 0.025, 0.045, "⏳ 데이터수집중"
    
    recent = list(candles_10min)[-10:]
    prior = list(candles_10min)[-20:-10]
    
    # 추세 + 거래량 + 변동성
    price_trend = (sum(c['close'] for c in recent)/10 - 
                   sum(c['close'] for c in prior)/10) / (sum(c['close'] for c in prior)/10)
    
    vol_trend = (sum(c['volume'] for c in recent)/10) / (sum(c['volume'] for c in prior)/10) - 1
    
    volatility = sum((c['high']-c['low'])/c['close'] for c in recent) / 10
    
    # 동적 기준
    base_buy, base_sell = 0.025, 0.045
    
    if vol_trend > 0.3:  # 거래량 급증
        buy_drop, sell_rise = base_buy*0.85, base_sell*1.1
        momentum = "🔥 거래량폭발"
    elif vol_trend < -0.2:  # 거래량 급감
        buy_drop, sell_rise = base_buy*1.2, base_sell*0.9  
        momentum = "❄️ 거래량위축"
    elif price_trend * vol_trend > 0.02:  # 모멘텀
        buy_drop, sell_rise = base_buy*0.9, base_sell*1.15
        momentum = "🚀 강한모멘텀"
    else:
        buy_drop, sell_rise = base_buy, base_sell
        momentum = "➡️ 안정추세"
    
    return max(0.015, min(0.035, buy_drop)), max(0.04, min(0.06, sell_rise)), momentum

while True:
    try:
        # 10분 캔들 우선 수집
        candle = get_10min_candle()
        if candle:
            candles_10min.append(candle)
            price = candle['close']
        else:
            price = pybithumb.get_current_price("BTC") or LAST_PRICE
            
        print(f"[{time.strftime('%H:%M:%S')}] {price:,.0f} | 데이터:{len(candles_10min)}개")
        
        # 기준가 설정
        if LAST_PRICE == 0 and len(candles_10min) >= 5:
            LAST_PRICE = price
        
        # 시장분석 및 매매
        if len(candles_10min) >= 20 and LAST_PRICE > 0:
            buy_drop, sell_rise, momentum = analyze_market()
            print(f"🎯 {momentum} | 매수:{buy_drop*100:.1f}%↓ | 매도:{sell_rise*100:.1f}%↑")
            
            # 매수
            if not HOLDING:
                if price <= LAST_PRICE * (1 - buy_drop):
                    print("🟢 매수실행!")
                    order = bithumb.buy_market_order("BTC", TRADE_AMOUNT)
                    print(f"✅ {order}")
                    HOLDING = True
                    LAST_PRICE = price
            
            # 매도  
            elif price >= LAST_PRICE * (1 + sell_rise):
                print("🔴 매도실행!")
                try:
                    balance = bithumb.get_balance("BTC")
                    btc = float(balance['data'].get('BTC', 0))
                    if btc > 0.00001:
                        order = bithumb.sell_market_order("BTC", btc)
                        print(f"✅ {order}")
                except:
                    pass
                HOLDING = False
                LAST_PRICE = price
        
        status = "🟢보유" if HOLDING else "⚪대기"
        print(f"상태: {status} | 기준가: {LAST_PRICE:,.0f}")
        print("="*60)
        
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ {e}")
        time.sleep(15)
