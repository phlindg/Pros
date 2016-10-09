import os
import urllib

import jinja2
import webapp2
from google.appengine.api import search
from google.appengine.ext import db

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

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
        self.render("templates/bas.html")


class Search(Handler):
    def get(self):
        players = Players.all().order('name')
        self.render('templates/playerss.html', players=players[0:10])

    def post(self):
        query = self.request.get('search')
        players = Players.by_name(query)
        self.render("templates/playerss.html", players=players[0:3])


class TeamSearch(Handler):
    def get(self):
        teams = Teams.all().order("t_name")
        self.render("templates/teams.html", teams=teams[0:10])

    def post(self):
        query = self.request.get('search')
        teams = Teams.by_name(query)
        self.render("templates/teams.html", teams=teams[0:3])

class PlayerFeed(Handler):
    def get(self):
        players = Players.all()
        self.render("templates/playerfeed.html", players=players)

def p_key(name="default"):
    return db.Key.from_path("players", name)




class Players(db.Model):
    name = db.StringProperty(required=True)
    mouse = db.StringProperty()
    keyboard = db.StringProperty()
    monitor = db.StringProperty()
    chair = db.StringProperty()
    p_img = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def by_name(cls, name):
        p = Players.all().filter('name >=', name)
        # sager egentligen find player where name = name
        return p

    def render(self):
        return render_str("templates/player.html", p=self)


class Teams(db.Model):
    t_name = db.StringProperty(required=True)
    players = db.StringProperty()
    t_img = db.BlobProperty()
    player_imgs = db.BlobProperty()

    @classmethod
    def by_name(cls, name):
        t = Teams.all().filter('t_name >=', name)
        return t

    def render(self):
        return render_str("templates/team.html", t=self)


class PlayerPage(Handler):
    def get(self, player_id):
        key = db.Key.from_path('Players', int(player_id), parent=p_key())
        player = db.get(key)

        if not player:
            self.error(404)
            return

        self.render("templates/player.html", player=player)


def CreateDocument(name):
    return search.Document(fields=[
        search.TextField(name="player", value=name)])


class Comment(Handler):
    """Handles requests to index comments."""

    def get(self):
        self.render("templates/testbas.html")

    def post(self):
        """Handles a post request."""

        player = self.request.get('name')
        query = self.request.get('search')
        if player:
            search.Index(name=INDEX_NAME).put(CreateDocument(player))
            self.render("templates/testbas.html", players=player)
        if query:
            self.redirect('/?' + urllib.urlencode(
                # {'query': query}))
                {'query': query.encode('utf-8')}))
        else:
            self.redirect('/')


class UploadPlayer(Handler):
    def get(self):
        self.render("templates/player_upload.html")

    def post(self):
        # p = Players()

        name = self.request.get("name")
        mouse = self.request.get("mouse")
        keyboard = self.request.get("keyboard")
        monitor = self.request.get("monitor")
        chair = self.request.get("chair")

        try:
            p_img = str(self.request.get("p_img"))
        except:
            self.error(500)
            # p_img = p_img.decode("utf-8")
            # p_img = images.resize(p_img, 16, 16)

        if name:
            p = Players(name=name, mouse=mouse, keyboard=keyboard, monitor=monitor, chair=chair, p_img=p_img)
            p.put()
            self.redirect("/home")


class UploadTeam(Handler):
    def get(self):
        self.render("templates/team_upload.html")

    def post(self):
        t_name = self.request.get("t_name")

        print("AWWDAWDAWDAWDADAWDAWD ", t_name)
        t_img = str(self.request.get("t_img"))

        if t_name:
            t = Teams(t_name=t_name, t_img=t_img)
            t.put()
            self.redirect("/home")


class Contacts(Handler):
    def get(self):
        self.render("templates/contact.html")


class FrontPage(Handler):
    def get(self):
        self.render("templates/frontpage.html")


app = webapp2.WSGIApplication([
    ('/', FrontPage),
    ('/home', MainPage),
    ('/uploadplayer', UploadPlayer),
    ('/playerfeed', PlayerFeed),
    ('/uploadteam', UploadTeam),
    ('/players/([0-9]+)', PlayerPage),
    ('/teamsearch', TeamSearch),
    ('/search', Search),
    ('/contact', Contacts)
], debug=True)
