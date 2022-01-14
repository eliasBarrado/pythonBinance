

class Order:

	def __init__(self, price, side, quantity, symbol, reduceOnly=False):

		self.symbol      = symbol
		self.price       = price
		self.side        = side
		self.quantity    = quantity
		self.reduceOnly  = reduceOnly
		self.type        = 'LIMIT'
		self.timeInForce = 'GTX'  # Post only order


	def send_to_binance(self,client):

		result = client.futures_create_order(
	        symbol     = self.symbol,
	        price      = self.price,
	        side       = self.side,
	        quantity   = self.quantity,
	        reduceOnly = self.reduceOnly,
	        type       = self.type,
	        timeInForce= self.timeInForce  # Post only order
    	)

		print(result)
		return result


