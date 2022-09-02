from datetime import datetime
import ccxt
import env
from pprint import pprint


class Binance:
    def __init__(self, account_name):
        self.exchange_obj = ccxt.binance(config={
            'apiKey': env.ACCESS_KEY_DICT.get(account_name).get("binance_api_key"),
            'secret': env.ACCESS_KEY_DICT.get(account_name).get("binance_secret"),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })
        self.fee_rate = 0.0004

    def buy_market_order(self, ticker, amount):
        info_dict = self.exchange_obj.create_market_buy_order(symbol=ticker, amount=amount)
        return info_dict['info']['orderId']

    def sell_market_order(self, ticker, amount):
        info_dict = self.exchange_obj.create_market_sell_order(symbol=ticker, amount=amount)
        return info_dict['info']['orderId']

    def get_order_detail_dict(self, ticker, order_id):
        record = self.exchange_obj.fetch_order(order_id, ticker)['info']
        order_dict = dict()
        order_dict['id'] = order_id
        order_dict['time'] = datetime.fromtimestamp(int(record['time']) / 1000)
        order_dict['fee'] = float(record['cumQuote']) * self.fee_rate
        order_dict['side'] = record['side']
        order_dict['cum_quote'] = record['cumQuote']
        order_dict['amount'] = float(record['executed_qty'])
        order_dict['avg_price'] = float(record['avgPrice'])
        return order_dict

