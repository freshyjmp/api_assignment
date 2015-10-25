import webapp2
from google.appengine.ext import ndb
import json
import urllib2
import datetime

class User(ndb.Model):
	email = ndb.StringProperty()
	last_updated = ndb.DateProperty()
	cash = ndb.FloatProperty(default=100000.00)
	balance = ndb.FloatProperty()
	rate_of_return = ndb.FloatProperty()
	portfolio = ndb.IntegerProperty(repeated=True)

class Order(ndb.Model):
	ticker = ndb.StringProperty()
	name = ndb.StringProperty()
	o_type = ndb.StringProperty()
	qty = ndb.IntegerProperty()
	open_date = ndb.DateTimeProperty()
	close_date = ndb.DateTimeProperty()
	price = ndb.FloatProperty()
	active = ndb.BooleanProperty()


class OrderHandler(webapp2.RequestHandler):
	def post(self, **kwargs):
		""" Creates an Order entity and adds it to the user's portfolio """

		if 'application/json' not in self.request.accept:
			self.response.status = 406
			message = {'error' : "Invalid Request, API only supports application/json" }
			self.response.write(json.dumps(message))
			return

		api_url = "http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol="
		
		ticker = self.request.get('ticker', default_value=None)
		qty = self.request.get('qty', default_value=None)
		o_type = self.request.get('o_type', default_value=None)
		
		if ticker is None:
			self.response.status = 400
			message = {'error' : "Must provide ticker, e.g. NFLX" }
			self.response.write(json.dumps(message))
			return
		if qty is None or qty <= 0:
			self.response.status = 400
			message = {'error' : "Must provide an integer quantity of shares" }
			self.response.write(json.dumps(message))
			return
		if o_type not in ['short', 'long']:
			self.response.status = 400
			message = {'error' : "Must provide order type, eg. short|long" }
			self.response.write(json.dumps(message))
			return

		if 'username' in kwargs:
			username = kwargs['username']
			u_key = ndb.Key(User, username)
			user = u_key.get()
			if user is None:
				self.response.status = 400
				message = {'error' : "User doesn't exist. Make user first." }
				self.response.write(json.dumps(message))
				return

			req = urllib2.Request(api_url + ticker)
			result = json.load(urllib2.urlopen(req))

			if 'Message' in result:
				message = {'error': "Bad request. Stock ticker invalid."}
				self.response.write(json.dumps(message))
			else:
				order = Order(ticker = result['Symbol'],
					name = result['Name'],
					o_type = o_type,
					qty = int(qty),
					open_date = datetime.datetime.now(),
					price = float(result['LastPrice']),
					active = True)

				o_key = order.put()
				out = order.to_dict()
				out['open_date'] = str(out['open_date'])
				cash_change = order.qty * (1 if order.o_type == "short" else -1 ) * order.price

				user.cash = user.cash + cash_change
				user.portfolio.append(o_key.id())
				user.put()
				self.response.write(json.dumps(out))

	def get(self, **kwargs):
		""" Displays information about an order """
		if 'application/json' not in self.request.accept:
			self.response.status = 406
			message = {'error' : "Invalid Request, API only supports application/json" }
			self.response.write(json.dumps(message))
			return

		if 'order' in kwargs:
			o_id = kwargs['order']
			o_key = ndb.Key(Order, int(o_id))
			order = o_key.get()
			out = order.to_dict()
			out['open_date'] = str(out['open_date'])
			self.response.write(json.dumps(out))
		elif 'username' in kwargs:
			username = kwargs['username']
			u_key = ndb.Key(User, username)
			user = u_key.get()
			if user is not None:
				orders = user.portfolio
				q = Order.query()
				results=[]
				for o_id in orders:
					o_key = ndb.Key(Order, int(o_id))
					order = o_key.get()
					out = order.to_dict()
					out['open_date'] = str(out['open_date'])
					results.append(out)
				self.response.write(json.dumps(results))
		else:
			q = Orders.query()
			keys = q.fetch(keys_only=True)
			results = {'orders': [x.id() for x in keys]}
			self.response.write(json.dumps(results))


class UserHandler(webapp2.RequestHandler):
	def post(self):
		""" Creates a User entity
		POST Body Variables
		username
		email
		password?
		"""
		if 'application/json' not in self.request.accept:
			self.response.status = 406
			message = {'error' : "Invalid Request, API only supports application/json" }
			self.response.status_message = "Invalid Request, API only supports application/json"
			return
		
		username = self.request.get('username', default_value=None)
		email = self.request.get('email', default_value=None)

		if username:
			u_key = ndb.Key(User, username)
			user = User(key=u_key)
			if u_key.get() is not None:
				self.response.status = 400
				message = {'error' : "Duplicate username. Please choose another username."}
				self.response.write(json.dumps(message))
				return
		else:
			self.response.status = 400
			message = {'error' : "Invalid Request, username is required"}
			self.response.write(json.dumps(message))
			return
		if email:
			user.email = email
		key = user.put()
		out = user.to_dict()
		self.response.write(json.dumps(out))
		return

	def get(self, **kwargs):
		if 'application/json' not in self.request.accept:
			self.response.status = 406
			message = {'error' : "Invalid Request, API only supports application/json" }
			self.response.write(json.dumps(message))
			return

		if 'id' in kwargs:
			out = ndb.Key(User, int(kwargs['id'])).get().to_dict()
			self.response.write(json.dumps(out))
		elif 'username' in kwargs:
			username = kwargs['username']
			u_key = ndb.Key(User, username)
			user = u_key.get()
			if user is not None:
				out = user.to_dict()
				self.response.write(json.dumps(out))
			else:
				self.response.status = 404
				message = {'error' : "No User found by that username."}
				self.response.write(json.dumps(message))
		else:
			q = User.query()
			keys = q.fetch(keys_only=True)
			results = {'users': [x.id() for x in keys]}
			self.response.write(json.dumps(results))

	def put(self, **kwargs):
		""" Updates User Entity
		PUT Body Variables
		email
		"""
		if 'application/json' not in self.request.accept:
			self.response.status = 406
			message = {'error' : "Invalid Request, API only supports application/json" }
			self.response.write(json.dumps(message)) 
			return

		email = self.request.get('email', default_value=None)

		if 'username' in kwargs:
			username = kwargs['username']
		elif username is None:
			self.response.status = 400
			message = {'error' : "Invalid Request, username is required" }
			self.response.write(json.dumps(message)) 
			return
		u_key = ndb.Key(User, username)
		user = User(key=u_key)
		if u_key.get() is not None:
			user.email = email
			key = user.put()
			out = user.to_dict()
			self.response.write(json.dumps(out))
			return
		else:
			user.email = email
			key = user.put()
			out = user.to_dict()
			self.response.write(json.dumps(out))
			return
		
	def delete(self, **kwargs):
		"""Deletes User Entity """
		if 'application/json' not in self.request.accept:
			self.response.status = 406
			message = {'error' : "Invalid Request, API only supports application/json" }
			self.response.write(json.dumps(message))
			return
		
		if 'username' in kwargs:
			username = kwargs['username']
		elif username is None:
			self.response.status = 400
			message = {'error' : "Invalid Request, username is required"}
			self.response.write(json.dumps(message))
			return
		u_key = ndb.Key(User, username)
		user = u_key.get()
		if user is not None:
			u_key.delete()



class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.write("Hello there!")


routes = [
    ('/', MainPage),
]

app = webapp2.WSGIApplication(routes, debug=True)
app.router.add(webapp2.Route(r'/user', UserHandler))
app.router.add(webapp2.Route(r'/user/', UserHandler))
app.router.add(webapp2.Route(r'/user/<id:[0-9]+><:/?>', UserHandler))
app.router.add(webapp2.Route(r'/user/<username:[a-z]+><:/?>', UserHandler))
app.router.add(webapp2.Route(r'/user/<username:[a-z]+>/orders', OrderHandler))
app.router.add(webapp2.Route(r'/user/<username:[a-z]+>/orders/', OrderHandler))
app.router.add(webapp2.Route(r'/user/<username:[a-z]+>/orders/<order:[0-9]+><:/?>', OrderHandler))
app.router.add(webapp2.Route(r'/order/<order:[0-9]+><:/?>', OrderHandler))

