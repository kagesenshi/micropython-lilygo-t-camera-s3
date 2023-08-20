import flask
from flask import request

app = flask.Flask("myapp")

@app.route('/', methods=["POST"])
def recv():
    print(request.get_json())
    return ""
