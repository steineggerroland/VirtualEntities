from flask import render_template
from flask.views import View


class ListView(View):
    def dispatch_request(self):
        things = []
        rooms = []
        persons = []
        return render_template("virtual_entities.html", entities={'things': things, 'rooms': rooms, 'persons': persons})
