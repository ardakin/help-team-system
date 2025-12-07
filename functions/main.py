from firebase_functions import https_fn
from firebase_functions.options import set_global_options
import flask

from app import app as flask_app  # app.py içindeki Flask instance

set_global_options(max_instances=10)


@https_fn.on_request()
def helppsys_app(req: https_fn.Request) -> https_fn.Response:
    with flask_app.request_context(req.environ):
        return flask_app.full_dispatch_request()
