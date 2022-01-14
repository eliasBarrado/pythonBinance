from flask import Flask
import binance
import time
import configparser

from binance import Client

import Order

config = configparser.ConfigParser()
config.read('config.txt')

client = Client(config['Binance']['api_key'], config['Binance']['api_secret'])

SYMBOL = 'ETHBUSD'
MAX_POSITION_SIZE = -0.1
ORDER_SIZE = 0.002
LIQUIDATION_ORDER_DISTANCE = 50


def create_order(price, side, quantity, reduceOnly=False):
    order = client.futures_create_order(
        symbol=SYMBOL,
        type='LIMIT',
        timeInForce='GTX',  # Post only order
        price=price,
        side=side,
        quantity=quantity,
        reduceOnly=reduceOnly
    )

    print(order)
    return order


def get_futures_position_information(symbol):

    result = client.futures_position_information(symbol=symbol)[0]

    result['liquidationPrice'] = round(float(result['liquidationPrice']), 2)
    result['positionAmt'] = float(result['positionAmt'])
    result['entryPrice'] = float(result['entryPrice'])
    result['unRealizedProfit'] = float(result['unRealizedProfit'])
    result['markPrice'] = round(float(result['markPrice']), 2)

    print(result)
    return result


def get_order_status(order):

    try:
        order = client.futures_get_order(symbol=SYMBOL, orderId=order['orderId'])
        return order['status']

    except binance.exceptions.BinanceAPIException as e:
        if(e.code == -2013):
            print(e.message)



def monitor_initial_position_order(order):

    position_information = get_futures_position_information(SYMBOL)

    while(float(order['price']) - position_information['markPrice'] < 3 and float(order['price']) - position_information['markPrice'] > 0):

        time.sleep(3)
        position_information = get_futures_position_information(SYMBOL)

    order_status = get_order_status(order)

    if(order_status == 'FILLED'):
        return "initial_position_order was filled"

    if(order_status in ['NEW', 'PARTIALLY_FILLED']):

        client.futures_cancel_order(symbol=SYMBOL, orderId=order['orderId'])
        return "initial_position_order was {} and cancelled".format(order_status)

    if(order_status in ['CANCELED', 'PENDING_CANCEL', 'REJECTED', 'EXPIRED']):
        return "initial_position_order was {}".format(order_status)

    return "ERROR:Check some error in monitor_initial_position_order"


def monitor_avoid_liquidation_order(avoid_liquidation_order):

    position_information = get_futures_position_information(SYMBOL)

    avoid_liquidation_order_status = get_order_status(avoid_liquidation_order)

    if(avoid_liquidation_order_status in ['FILLED', 'PARTIALLY_FILLED']):
        return "avoid_liquidation_order was {}".format(avoid_liquidation_order_status)

    while(abs(position_information['liquidationPrice'] - position_information['markPrice']) < LIQUIDATION_ORDER_DISTANCE):

        time.sleep(1)

        avoid_liquidation_order_status = get_order_status(avoid_liquidation_order)

        if(avoid_liquidation_order_status in ['FILLED', 'PARTIALLY_FILLED']):
            return "avoid_liquidation_order was {}".format(avoid_liquidation_order_status)

        position_information = get_futures_position_information(SYMBOL)

    if(avoid_liquidation_order_status not in ['FILLED', 'PARTIALLY_FILLED']):
        print("Liquidation not close... Canceling avoid_liquidation_order")
        cancel = client.futures_cancel_order(symbol=SYMBOL, orderId=avoid_liquidation_order['orderId'])

    return None


def monitor_closing_position_order(closing_position_order):

    position_information = get_futures_position_information(SYMBOL)

    while(position_information['markPrice'] - float(closing_position_order['price']) < 2 and position_information['markPrice'] > float(closing_position_order['price'])):

        closing_position_order_status = get_order_status(closing_position_order)

        if(closing_position_order_status == 'FILLED'):
            return "closing_position_order was filled"

        time.sleep(1)
        position_information = get_futures_position_information(SYMBOL)

    closing_position_order_status = get_order_status(closing_position_order)

    if(closing_position_order_status == 'FILLED'):
        return "closing_position_order was filled"

    if(closing_position_order_status in ['NEW', 'PARTIALLY_FILLED']):

        client.futures_cancel_order(symbol=SYMBOL, orderId=closing_position_order['orderId'])
        return "closing_position_order was {} and cancelled".format(closing_position_order_status)

    if(closing_position_order_status in ['CANCELED', 'PENDING_CANCEL', 'REJECTED', 'EXPIRED']):
        return "closing_position_order was {}".format(closing_position_order_status)

    return "ERROR:Check some error in monitor_closing_position_order"


position_information = get_futures_position_information(SYMBOL)

#order = create_order(4027,'BUY',0.002)

#a = client.futures_get_order(symbol=SYMBOL,orderId=order['orderId'])
# print(a)


#result = client.futures_cancel_order(symbol=SYMBOL,orderId='2314693515')
# print(result)
#orders = client.futures_get_open_orders(symbol=SYMBOL)
# print(orders)

#result = client.futures_change_margin_type(symbol=SYMBOL,marginType='ISOLATED')
# print(result)

#result = client.futures_change_leverage(symbol=SYMBOL, leverage='25')
# print(result)


def run():
    while(True):

        try:

            position_information = get_futures_position_information(SYMBOL)

            while(abs(position_information['positionAmt']) < ORDER_SIZE):

                print("Bootstraping...\n")

                order = create_order(position_information['markPrice'] + 1, 'SELL', ORDER_SIZE)

                monitor_position_order_result = monitor_initial_position_order(order)

                print(monitor_position_order_result)

                time.sleep(1)

                position_information = get_futures_position_information(SYMBOL)

            while(position_information['unRealizedProfit'] < 0.01):

                print("position_information['unRealizedProfit'] < 0.01 \n")

                if(abs(position_information['positionAmt'] - MAX_POSITION_SIZE) > position_information['positionAmt']*0.5):

                    if(position_information['liquidationPrice'] - position_information['markPrice'] < LIQUIDATION_ORDER_DISTANCE):

                        print("Liquidation is close...creating order.")

                        avoid_liquidation_order = create_order(position_information['liquidationPrice'] - 2, 'SELL', max(round(-position_information['positionAmt']*0.25,3), ORDER_SIZE))

                        avoid_liquidation_order_result = monitor_avoid_liquidation_order(avoid_liquidation_order)
                        print(avoid_liquidation_order_result)

                    else:
                        print("Liquidation not close...Waiting 3 seconds")
                        time.sleep(3)
                else:
                    print("MAX_POSITION_SIZE reached")
                    break

                position_information = get_futures_position_information(SYMBOL)

            while(position_information['unRealizedProfit'] >= 0.01):

                print("position_information['unRealizedProfit'] >= 0.01 \n ")

                closing_position_order = create_order(position_information['markPrice'] - 1, 'BUY', -position_information['positionAmt'], True)

                closing_position_order_result = monitor_closing_position_order(closing_position_order)
                print(closing_position_order_result)

                time.sleep(5)

                position_information = get_futures_position_information(SYMBOL)

        except Exception as e:
            print(e)


app = Flask(__name__)

@app.route('/test')
def test():
    order = {'orderId': 2670839848}
    try:
        get_order_status(order)
    except binance.exceptions.BinanceAPIException as e:
        if(e.code == -2013):
            print(e.message)

@app.route('/test2')
def test2():
    order = Order.Order(4000,'SELL', ORDER_SIZE, SYMBOL)
    order = order.send_to_binance(client)
    return str(order)
        

@app.route('/_ah/start')
def start():
    print('Call to /_ah/start')
    run()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
