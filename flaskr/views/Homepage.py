from flask import redirect, url_for
from flask.views import View


class Homepage(View):
    def __init__(self):
        pass

    def dispatch_request(self):
        return redirect(url_for("ve_list"))
