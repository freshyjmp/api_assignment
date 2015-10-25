import webapp2
from google.appengine.ext import ndb
import json
import urllib2

class User(ndb.Model):
	email = ndb.StringProperty()
	last_updated = ndb.DateProperty()
	cash = ndb.FloatProperty()
	balance = ndb.FloatProperty()
	rate_of_return = ndb.FloatProperty()
	portfolio = ndb.KeyProperty(repeated=True)

class Orders(ndb.Model):
	ticker = ndb.StringProperty()
	name = ndb.StringProperty()
	o_type = ndb.StringProperty()
	qty = ndb.IntegerProperty()
	open_date = ndb.DateTimeProperty()
	close_date = ndb.DateTimeProperty()
	price = ndb.FloatProperty()
	active = ndb.BooleanProperty()


class OrderHandler(webapp2.RequestHandler):
	def post(self):
		""" Creates an Order entity and adds it to the user's portfolio """

		if 'application/json' not in self.request.accept:
			self.response.status = 406
			self.response.status_message = "Invalid Request, API only supports application/json"
			return

		api_url = "http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol="
		
		ticker = self.request.get('ticker', default_value=None)
		qty = self.request.get('qty', default_value=None)
		o_type = self.request.get('o_type', default_value=None)
		
		if ticker is None:
			self.reponse.status = 400
			self.response.status_message = "Must provide ticker, e.g. NFLX"
			return
		if qty is None:
			self.response.status = 400
			self.response.status_message = "Must provide an integer quantity of shares"
			return
		if o_type is None:
			self.response.status = 400
			self.response.status_mesage = "Must provide order type, eg. short|long"
			return

		if 'username' in kwargs:
			username = kwargs['username']
			u_key = ndb.Key(User, username)
			user = u_key.get()
			if user is not None:

			else:
				self.response.status = 404
				self.response.status_message ="No User found by that username."



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
			self.response.status_message = "Invalid Request, API only supports application/json"
			return
		
		username = self.request.get('username', default_value=None)
		email = self.request.get('email', default_value=None)

		if username:
			u_key = ndb.Key(User, username)
			user = User(key=u_key)
			if u_key.get() is not None:
				self.restponse.status = 400
				self.response.status_message = "Duplicate username. Please choose another username."
				return
		else:
			self.response.status = 400
			self.response.status_message = "Invalid Request, username is required"
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
			self.response.status_message = "Invalid Request, API only supports application/json"
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
				self.response.status_message ="No User found by that username."
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
			self.response.status_message = "Invalid Request, API only supports application/json"
			return

		email = self.request.get('email', default_value=None)

		if 'username' in kwargs:
			username = kwargs['username']
		elif username is None:
			self.response.status = 400
			self.response.status_message = "Invalid Request, username is required"
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
			self.response.status_message = "Invalid Request, API only supports application/json"
			return
		
		if 'username' in kwargs:
			username = kwargs['username']
		elif username is None:
			self.response.status = 400
			self.response.status_message = "Invalid Request, username is required"
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
