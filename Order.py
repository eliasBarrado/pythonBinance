import binance

class Order:

	def __init__(self, price, side, quantity, symbol, reduceOnly=False):

		self.symbol      = symbol
		self.price       = price
		self.side        = side
		self.quantity    = quantity
		self.reduceOnly  = reduceOnly
		self.type        = 'LIMIT'
		self.timeInForce = 'GTX'  # Post only order
		


	def send_to_binance(self, client):

		result = client.futures_create_order(
	        symbol     = self.symbol,
	        price      = self.price,
	        side       = self.side,
	        quantity   = self.quantity,
	        reduceOnly = self.reduceOnly,
	        type       = self.type,
	        timeInForce= self.timeInForce  # Post only order
    	)

		self.result = result
		self.orderId = result['orderId']
		self.status =  result['status']

		print(result)
		return result


	def update_on_binance(self, client):

		try:
			order = client.futures_get_order(symbol=self.symbol, orderId=self.orderId)
			self.status = order['status']
        	

		except binance.exceptions.BinanceAPIException as e:
			if(e.code == -2013):
				print(e.message)

	def get_status(self):
		return self.status

	def get_price(self):
		return self.price


	def cancel(self, client):
		order = client.futures_cancel_order(symbol=self.symbol, orderId=self.orderId)
		self.status = order['status']
			
			

	


