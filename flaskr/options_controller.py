import re
from http import HTTPStatus

from flask import Blueprint, redirect, request, session, make_response
from urllib3.util import Url, parse_url

PARAMS = ['refresh_interval', 'fullscreen', 'dark_mode']


def options_blueprint():
    api = Blueprint('options', __name__)

    def adapt_request_arg_to_session(param):
        arg = request.args.get(param)
        if arg == 'false' and param in session:
            del session[param]
            return False
        elif arg != 'false':
            session[param] = arg
            return True

    def add_param(param, url: Url):
        query = f'{param}={session[param]}' if url.query is None or len(url.query) == 0 \
            else f'{url.query}&{param}={session[param]}'
        return Url(scheme=url.scheme, host=url.host, port=url.port, path=url.path, query=query,
                   fragment=url.fragment)

    def remove_param(param, url: Url):
        query = re.sub(r'(&)?' + param + r'=(\w|\d)+', '', url.query)
        return Url(scheme=url.scheme, host=url.host, port=url.port, path=url.path, query=query,
                   fragment=url.fragment)

    @api.post('')
    def toggle_param():
        url = parse_url(request.headers.get('Referer'))
        for param in filter(lambda p: p in request.args, PARAMS):
            if not adapt_request_arg_to_session(param):
                url = remove_param(param, url)
        return redirect(url.request_uri)

    @api.before_app_request
    def add_params():
        if request.method == 'GET' and request.url.find('.html') >= 0:
            for param in list(filter(lambda p: p in request.args and p not in session, PARAMS)):
                adapt_request_arg_to_session(param)
            session_params_not_in_url = list(filter(lambda p: p in session and p not in request.args, PARAMS))
            if session_params_not_in_url:
                url = parse_url(request.url)
                for param in session_params_not_in_url:
                    url = add_param(param, url)
                return redirect(url.request_uri, code=HTTPStatus.TEMPORARY_REDIRECT)

    return api
