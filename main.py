from pybit.unified_trading import HTTP
import pandas as pd
import schedule
import time
import datetime
import math

session = HTTP(
  testnet=False,
  api_key="",
  api_secret="",
)

prices = None
ema25 = None
ema50 = None
ema100 = None

min_gap = 0.07
PL = 1.5
fee = 0.048
leverage = 10
unit = 0.025


def floor(x, z):
  z = 10**z
  return math.floor(x * z) / z


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
    category="linear",
    symbol="BTCUSDT",
    side="Buy",
    orderType="Market",
    qty=str(qty),
    price=str(price),
    stopLoss=str(stoploss),
    takeProfit=str(takeprofit),
  )


def place_short(price, qty, stoploss, takeprofit):
  session.place_order(
    category="linear",
    symbol="BTCUSDT",
    side="Sell",
    orderType="Market",
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
  print('ema25 :', floor(ema25[198], 1))
  print('ema50 :', floor(ema50[198], 1))
  print('ema100 :', floor(ema100[198], 1))
  print('regular :', is_regula())
  print('invert :', is_invert())
  print('25,50 gap :', floor(gap_25_50(), 3))
  print('100,50 gap :', floor(gap_50_100(), 3))
  if is_no_position():
    if is_long():
      place_long(
        float(prices[-1][4]), unit, floor(ema50[198], 1),
        floor(
          float(prices[-1][4]) + (float(prices[-1][4]) - ema50[198]) * PL, 1))
      print('long:', prices[-1][4], unit)
    elif is_short():
      place_short(
        float(prices[-1][4]), unit, floor(ema50[198], 1),
        floor(
          float(prices[-1][4]) + (float(prices[-1][4]) - ema50[198]) * PL, 1))
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
  ema25 = df[4].ewm(span=25).mean().to_list()
  ema50 = df[4].ewm(span=50).mean().to_list()
  ema100 = df[4].ewm(span=100).mean().to_list()


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
    if gap_25_50() >= min_gap and gap_50_100() >= min_gap:
      if float(prices[-1][1]) < floor(ema25[198], 1) < float(prices[-1][4]):
        return True
  return False


def is_short():
  if is_invert():
    if gap_25_50() >= min_gap and gap_50_100() >= min_gap:
      if float(prices[-1][1]) < floor(ema25[198], 1) < float(prices[-1][4]):
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
