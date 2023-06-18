from pybit.unified_trading import HTTP
import pandas as pd
import schedule
import time
import datetime
import math

# 1. 기본적인 API 연동
# 2. EMA 구현 O

# 매매법
# 25ema > 50ema > 100ema == 정배열
# 25ema < 50ema < 100ema == 역배열

# 정배열 and 캔들이 25ema 위 == 상승 추세
# 역배열 and 캔들이 25ema 아래 = 하락 추세

# 상승 추세 일때 캔들이 25ema와 50ema 사이에 들어오고 다시 25ema까지 올라면 종가에서 롱포지션 진입
# 하락 추세 일때 캔들이 25ema와 50ema 사이에 들어오고 다시 25ema아래로 내려가면 종가에서 숏포지션 진입

# 포지션 진입시 50ema에 스탑로스를 걸고 스탑로스 1.5배 만큼 익절라인을 지정

session = HTTP(
  testnet=False,
  api_key="",
  api_secret="",
)

prices = None
ema25 = None
ema50 = None
ema100 = None

min_gap = 1
PL = 1.5
fee = 0.048
leverage = 10
unit = 0.02


def set_leverage(leverage):
  session.set_leverage(
    category="linear",
    symbol="BTCUSDT",
    buyLeverage=str(leverage),
    sellLeverage=str(leverage),
  )


def is_no_position():
  result = session.get_positions(
    category="linear",
    symbol="BTCUSDT",
  )

  if float(result['result']['list'][0]['size']) == 0 and float(
      result['result']['list'][1]['size']) == 0:
    return True

  return False


def place_long(price, qty, stoploss, takeprofit):
  session.place_order(
    category="linear",  #선물
    symbol="BTCUSDT",
    side="Buy",
    orderType="Market",  #지정가
    qty=str(qty),
    price=str(price),
    stopLoss=str(stoploss),
    takeProfit=str(takeprofit),
  )


def place_short(price, qty, stoploss, takeprofit):
  session.place_order(
    category="linear",  #선물
    symbol="BTCUSDT",
    side="Sell",
    orderType="Market",  #지정가
    qty=str(qty),
    price=str(price),
    stopLoss=str(stoploss),
    takeProfit=str(takeprofit),
  )


def update():
  update_price(5, 200)
  update_ema()
  print(datetime.datetime.now())
  print('price :', prices[-1][4])
  print('ema25 :', ema25[198])
  print('ema50 :', ema50[198])
  print('ema100 :', ema100[198])
  print('regular :', is_regula())
  print('invert :', is_invert())
  print('25,50 gap :', gap_25_50())
  print('100,50 gap :', gap_50_100())
  if is_no_position():
    if is_long():
      place_long(
        prices[-1][4], unit, math.floor(ema50[198], 1),
        prices[-1][4] + math.floor((prices[-1][4] - ema50[198]) * 1.015, 1))
      print('long:', prices[-1][4], unit)
    elif is_short():
      place_short(
        prices[-1][4], unit, math.floor(ema50[198], 1),
        prices[-1][4] + math.floor((prices[-1][4] - ema50[198]) * 1.015, 1))
      print('short:', prices[-1][4], unit)


def update_price(interval, limit):
  result = session.get_kline(
    category="linear",
    symbol="BTCUSDT",
    interval=interval,
    limit=limit,
  )

  global prices
  prices = list(reversed(result['result']['list'][1:]))


def update_ema():
  global ema25, ema50, ema100
  df = pd.DataFrame(prices)
  ema25 = df[4].ewm(25).mean()
  ema50 = df[4].ewm(50).mean()
  ema100 = df[4].ewm(100).mean()


def is_regula():
  if ema25[198] > ema50[198] > ema100[198]:
    return True
  else:
    return False


def is_invert():
  if ema25[198] < ema50[198] < ema100[198]:
    return True
  else:
    return False


def gap_25_50():
  return abs(ema25[198] / ema50[198] - 1) * 100


def gap_50_100():
  return abs(ema100[198] / ema50[198] - 1) * 100


def is_long():
  if is_regula():
    if ema25[198] < float(prices[-1][4]) and ema25[197] > float(prices[-2][4]):
      if gap_25_50() >= min_gap and gap_50_100() >= min_gap:
        return True
  return False


def is_short():
  if is_invert():
    if ema25[198] > float(prices[-1][4]) and ema25[197] < float(prices[-2][4]):
      if gap_25_50() >= min_gap and gap_50_100() >= min_gap:
        return True
  return False


update()

for h in range(24):
  for m in range(0, 60, 5):
    if h < 10 and m < 10:
      schedule.every().day.at("0" + str(h) + ":0" + str(m) + ":01").do(update)
    elif h < 10 and m >= 10:
      schedule.every().day.at("0" + str(h) + ":" + str(m) + ":01").do(update)
    elif h >= 10 and m < 10:
      schedule.every().day.at(str(h) + ":0" + str(m) + ":01").do(update)
    elif h >= 10 and m >= 10:
      schedule.every().day.at(str(h) + ":" + str(m) + ":01").do(update)

while True:
  schedule.run_pending()
  time.sleep(1)
