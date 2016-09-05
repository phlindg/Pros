import webapp2
import jinja2
import os
import sys
import urllib
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import search

jinja_env = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)

INDEX_NAME = "player"
def render_str(template, **params):
		t = jinja_env.get_template(template)
		return t.render(**params)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(**params)
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class MainPage(Handler):
	def get(self):
		players = Players.all().order('name')
		self.render('templates/playerss.html',players = players)

def p_key(name="default"):
	return db.Key.from_path("players", name)

class Players(db.Model):
	name = db.StringProperty(required = True)
	mouse = db.StringProperty()
	keyboard = db.StringProperty()
	monitor = db.StringProperty()
	chair = db.StringProperty()
	p_img = db.BlobProperty()
	date = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)

	@classmethod
	def by_name(cls, name):
		p = Players.all().filter('name =', name).get()
		#sager egentligen find player where name = name
		return p
	def render(self):
		return render_str("templates/player.html", p = self)


class PlayerPage(Handler):
	def get(self, player_id):
		key = db.Key.from_path('Players', int(player_id), parent = p_key())
		player = db.get(key)

		if not player:
			self.error(404)
			return

		self.render("templates/testplayer.html", player = player)


def CreateDocument(name):
	return search.Document(fields=[
		search.TextField(name="player", value=name)])
class Comment(Handler):
    """Handles requests to index comments."""

    def post(self):
        """Handles a post request."""
        
        player = self.request.get('name')
        query = self.request.get('search')
        if content:
            search.Index(name=_INDEX_NAME).put(CreateDocument(player))
        if query:
            self.redirect('/?' + urllib.urlencode(
                #{'query': query}))
                {'query': query.encode('utf-8')}))
        else:
            self.redirect('/')


class Upload(Handler):
	def get(self):
		self.render("templates/player_upload.html")

	def post(self):
		#p = Players()

		name = self.request.get("name")
		mouse = self.request.get("mouse")
		keyboard = self.request.get("keyboard")
		monitor = self.request.get("monitor")
		chair = self.request.get("chair")

		#query = self.request.get("search")



		try:
			p_img = str(self.request.get("p_img"))
		except:
			self.error(500)
		#p_img = p_img.decode("utf-8")
		#p_img = images.resize(p_img, 16, 16)


		if name:
			p = Players(name = name, mouse = mouse, keyboard = keyboard, monitor = monitor, chair = chair, p_img = p_img)
			p.put()
		#	search.Index(name=INDEX_NAME).put(CreateDocument(name))
			#self.redirect("/players/%s" % str(p.key().id()))
	#	if query:
	#		self.redirect("/players/?" + urllib.urlencode(
	#			{'query' : query.encode("utf-8")}))
			


app = webapp2.WSGIApplication([
	('/', MainPage),
	('/upload', Upload),
	('/players/([0-9]+)', PlayerPage)
	], debug = True)