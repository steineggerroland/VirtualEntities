import re
from http import HTTPStatus

from flask import Blueprint, redirect, request
from urllib3.util import Url, parse_url


def options_blueprint():
    api = Blueprint('options', __name__)

    @api.post('/refresh-interval')
    def refresh_interval():
        return redirect(toggle_param_in_query('refresh_interval', parse_url(
            request.headers.get('Referer'))).request_uri)

    @api.post('/fullscreen')
    def fullscreen():
        return redirect(toggle_param_in_query('fullscreen', parse_url(
            request.headers.get('Referer'))).request_uri)

    def toggle_param_in_query(param, url: Url):
        if param in request.args:
            query = f'{param}={request.args[param]}' if url.query is None or len(url.query) == 0 \
                else f'{url.query}&{param}={request.args[param]}'
        else:
            query = re.sub(r'(&)?' + param + r'=(\w|\d)+', '', url.query)
        return Url(scheme=url.scheme, host=url.host, port=url.port, path=url.path, query=query,
                   fragment=url.fragment)

    return api
