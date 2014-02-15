from flask import request

from pyoseo import app

@app.route('/')
@app.route('/index')
def index():
    return 'Hello World!'

@app.route('/oseo', methods=['POST',])
def oseo_endpoint():
    return 'This is pyoseo'
