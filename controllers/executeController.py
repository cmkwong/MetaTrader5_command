
import MetaTrader5 as mt5

class Mt5Executor:
    def __init__(self, type_filling):
        self.type_filling = type_filling

    def requests_format(self, strategy_id, lots, close_pos=False):
        """
        :param strategy_id: str, belong to specific strategy
        :param lots: [float]
        :param close_pos: Boolean, if it is for closing position, it will need to store the position id for reference
        :return: requests, [dict], a list of request
        """
        # the target with respect to the strategy id
        symbols = self.strategy_symbols[strategy_id]

        # type of filling
        tf = None
        if self.type_filling == 'fok':
            tf = mt5.ORDER_FILLING_FOK
        elif self.type_filling == 'ioc':
            tf = mt5.ORDER_FILLING_IOC
        elif self.type_filling == 'return':
            tf = mt5.ORDER_FILLING_RETURN
        # building each request
        requests = []
        for symbol, lot, deviation in zip(symbols, lots, self.deviations[strategy_id]):
            if lot > 0:
                action_type = mt5.ORDER_TYPE_BUY # int = 0
                price = mt5.symbol_info_tick(symbol).ask
            elif lot < 0:
                action_type = mt5.ORDER_TYPE_SELL # int = 1
                price = mt5.symbol_info_tick(symbol).bid
                lot = -lot
            else:
                raise Exception("The lot cannot be 0") # if lot equal to 0, raise an Error
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': float(lot),
                'type': action_type,
                'price': price,
                'deviation': deviation, # indeed, the deviation is useless when it is marketing order, note 73d
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": tf,
            }
            if close_pos:
                if self.position_ids[strategy_id][symbol] == -1:
                    continue    # if there is no order id, do not append the request, note 63b (default = 0)
                request['position'] = self.position_ids[strategy_id][symbol] # note 61b
            requests.append(request)
        return requests

    def requests_execute(self, requests):
        """
        :param requests: [request]
        :return: Boolean
        """
        # execute the request first and store the results
        results = []
        for request in requests:
            result = mt5.order_send(request)  # sending the request
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("order_send failed, symbol={}, retcode={}".format(request['symbol'], result.retcode))
                return results
            results.append(result)
        # print the results
        for request, result in zip(requests, results):
            print("Action: {}; by {} {:.2f} lots at {:.5f} ( ptDiff={:.1f} ({:.5f}(request.price) - {:.5f}(result.price) ))".format(
                request['type'], request['symbol'], result.volume, result.price,
                (request['price'] - result.price) * 10 ** mt5.symbol_info(request['symbol']).digits,
                request['price'], result.price)
            )
        return results