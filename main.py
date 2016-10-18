import hashlib
import hmac
import os
import random
import urllib
from string import letters

import jinja2
import webapp2
from google.appengine.api import search
from google.appengine.ext import db

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

INDEX_NAME = "player"
secret = "awoop"


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(**params)


def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):  ##Denna kollar om usern e inloggad varenda gong den gor ngt.
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and Users.by_id(int(uid))


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


def u_key(group="default"):  # Denna skapar objektet som storar alla users.
    return db.Key.from_path('users', group)


def t_key(group="default"):  # Denna skapar objektet som storar alla users.
    return db.Key.from_path('teams', group)


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

    @classmethod
    def by_id(cls, pid):
        return Players.get_by_id(pid, parent=p_key())

    @classmethod
    def delete_by_id(cls,pid):
        Players.get_by_id(pid, parent=p_key()).key.delete()

    def render(self):
        return render_str("templates/player.html", p=self)


class Teams(db.Model):
    t_name = db.StringProperty(required=True)
    t_players = db.ListProperty(db.Key)
    playars = db.ReferenceProperty(Players)
    t_img = db.BlobProperty()
    player_imgs = db.BlobProperty()

    @classmethod
    def by_name(cls, name):
        t = Teams.all().filter('t_name >=', name)
        return t

    @classmethod
    def by_id(cls, tid):
        return Teams.get_by_id(tid, parent=t_key())

    def render(self):
        return render_str("templates/team.html", t=self)



def makeSalt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))


def makePWHash(name, pw, salt=None):
    if not salt:
        salt = makeSalt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def validPW(name, pw, h):
    salt = h.split(',')[0]
    return h == makePWHash(name, pw, salt)


class Users(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return Users.get_by_id(uid, parent=u_key())

    @classmethod
    def by_name(cls, name):
        user = Users.all().filter("name = ", name).get()
        return user

    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = makePWHash(name, pw)
        return Users(parent=u_key(),
                     name=name,
                     pw_hash=pw_hash,
                     email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and validPW(name, pw, u.pw_hash):
            return u


cal = Users.register("calsan123", "haohao123", "mail@mail.com")
#if not cal:
cal.put()


class PlayerPage(Handler):
    def get(self, player_id):
        key = db.Key.from_path('Players', int(player_id), parent=p_key())
        player = db.get(key)
        if not player:
            self.error(404)
            return


        self.render("templates/playerpage.html", p=player)


class TeamPage(Handler):
    def get(self, team_id):
        key = db.Key.from_path('Teams', int(team_id), parent=t_key())
        team = db.get(key)
        self.render("templates/teampage.html", t=team)


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

        if self.user:
            self.render("templates/player_upload.html")
        else:
            self.redirect("/home")

    def post(self):
        if not self.user:
            self.redirect('/home')

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
            p = Players(parent=p_key(), name=name, mouse=mouse, keyboard=keyboard, monitor=monitor, chair=chair,
                        p_img=p_img)
            p.put()
            self.redirect("/home")


class UploadTeam(Handler):
    def get(self):
        if self.user:
            self.render("templates/team_upload.html")
        else:
            self.redirect("/home")

    def post(self):

        t_name = self.request.get("t_name")
        t_player1 = self.request.get("t_player1")
        p1 = Players.by_name(t_player1).get().key()
        t_player2 = self.request.get("t_player2")
        p2 = Players.by_name(t_player2).get().key()
        t_player3 = self.request.get("t_player3")
        p3 = Players.by_name(t_player3).get().key()
        t_player4 = self.request.get("t_player4")
        p4 = Players.by_name(t_player4).get().key()
        t_player5 = self.request.get("t_player5")
        p5 = Players.by_name(t_player5).get().key()
        t_player6 = self.request.get("t_player6")
        p6 = Players.by_name(t_player6).get().key()


        t_players = [p1, p2, p3, p4, p5, p6]
        playars = db.get(p1)

        t_img = str(self.request.get("t_img"))

        if t_name:
            t = Teams(parent=t_key(), t_name=t_name, t_img=t_img, t_players = t_players, playars = playars)
            t.put()
            self.redirect("/home")


class Contacts(Handler):
    def get(self):
        self.render("templates/contact.html")


class FrontPage(Handler):
    def get(self):
        self.render("templates/frontpage.html")


############################### LOGIN STUFF ##############################################################




class Login(Handler):
    def get(self):
        self.render('templates/login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = Users.login(username, password)
        if u:
            self.login(u)  # denna placerar cookien
            self.redirect('/home')
        else:
            msg = 'Invalid login'
            self.render('templates/login-form.html', error=msg)


class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect("/home")


##########################################################################################################

class Admin(Handler):
    def get(self):
        self.render("templates/adminbas.html")


app = webapp2.WSGIApplication([
    ('/', FrontPage),
    ('/home/?', MainPage),
    ('/uploadplayer', UploadPlayer),
    ('/playerfeed', PlayerFeed),
    ('/uploadteam', UploadTeam),
    ('/players/([0-9]+)', PlayerPage),
    ('/teams/([0-9]+)', TeamPage),
    ('/teamsearch', TeamSearch),
    ('/search', Search),
    ('/contact', Contacts),
    # ('/signup', Register),
    ('/login', Login),
    ('/logout', Logout),
    ('/admin', Admin)
], debug=True)
