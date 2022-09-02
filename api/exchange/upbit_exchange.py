import pyupbit
import env
from pprint import pprint


class Upbit:
    def __init__(self, account_name):
        self.exchange_obj = pyupbit.Upbit(env.ACCESS_KEY_DICT.get(account_name).get("api_key"),
                                          env.ACCESS_KEY_DICT.get(account_name).get("secret"))
        self.fee_rate = 0.0005

    def buy_market_order(self, ticker, cost):
        """
        :param ticker: 가상화폐 티커
        :param cost: 원화 매수 총액 5,000 won
        :return:
        """
        info_dict = self.exchange_obj.buy_market_order(ticker, cost, 1)
        return info_dict['uuid']

    def sell_market_order(self, ticker, amount):
        """
        :param ticker: 가상화폐 티커
        :param amount: 매도 수량 0.001BTC
        :return:
        """
        info_dict = self.exchange_obj.sell_market_order(ticker, amount, 1)
        return info_dict['uuid']

    def get_order_detail_dict(self, order_id):
        exchange_order_dict = self.exchange_obj.get_order(ticker_or_uuid=order_id)["trades"][0]
        order_dict = dict()
        order_dict['id'] = order_id
        order_dict['time'] = exchange_order_dict["created_at"]
        order_dict['amount'] = float(exchange_order_dict["volume"])
        order_dict['cum_quote'] = float(exchange_order_dict["price"]) * float(exchange_order_dict["volume"])
        order_dict['side'] = "buy" if exchange_order_dict["side"] == "bid" else "sell"
        order_dict['avg_price'] = float(exchange_order_dict["price"])
        order_dict['fee'] = order_dict['cum_quote'] * self.fee_rate
        return order_dict


if "__main__" == __name__:
    upbit = Upbit(account_name="minsung")
    # order_dict = upbit.get_order_detail_dict(order_id='1400eb2d-b2ff-4fe5-8fa9-ac13f1645959')
    # pprint(order_dict)



# ({'created_at': '2022-09-02T16:33:27.787524+09:00',
#   'executed_volume': '0',
#   'locked': '5002.5',
#   'market': 'KRW-BTC',
#   'ord_type': 'price',
#   'paid_fee': '0',
#   'price': '5000',
#   'remaining_fee': '2.5',
#   'reserved_fee': '2.5',
#   'side': 'bid',
#   'state': 'wait',
#   'trades': [],
#   'trades_count': 0,
#   'uuid': '1400eb2d-b2ff-4fe5-8fa9-ac13f1645959'},
#  {'group': 'order', 'min': 199, 'sec': 7})


# {'amount': None,
#  'average': None,
#  'clientOrderId': None,
#  'cost': 12000.0,
#  'datetime': '2022-09-02T07:22:22.000Z',
#  'fee': {'cost': 0.0, 'currency': 'KRW'},
#  'filled': 0.0,
#  'id': 'f8a35e57-6e21-4d7c-9c12-74e052ac44fe',
#  'info': {'created_at': '2022-09-02T16:22:22+09:00',
#           'executed_volume': '0.0',
#           'locked': '12006.0',
#           'market': 'KRW-BTT',
#           'ord_type': 'price',
#           'paid_fee': '0.0',
#           'price': '12000.0',
#           'remaining_fee': '6.0',
#           'remaining_volume': None,
#           'reserved_fee': '6.0',
#           'side': 'bid',
#           'state': 'wait',
#           'trades_count': '0',
#           'uuid': 'f8a35e57-6e21-4d7c-9c12-74e052ac44fe',
#           'volume': None},
#  'lastTradeTimestamp': None,
#  'postOnly': None,
#  'price': None,
#  'remaining': None,
#  'side': 'buy',
#  'status': 'open',
#  'stopPrice': None,
#  'symbol': 'BTT/KRW',
#  'timeInForce': None,
#  'timestamp': 1662103342000,
#  'trades': [],
#  'type': 'market'}
