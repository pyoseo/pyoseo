'''
pyoseo, a flask-based OGC OSEO server.

* create the database and populate it with sample data:
  .. code: bash
     
     $ python createdb.py
     $ sqlite3 pyoseo/sqlite.db < fixtures/test_data.sql

* get the test server running
  .. code: bash

     $ python runserver.py

* test the server
  .. code: bash

     $ curl --include --header "Content-Type: application/xml" \
            --data @samples/SampleData/GetStatus.xml http://localhost:5000/oseo

* Alternatively you can test in python, using the requests library:
  .. code: python

     import requests
     msg = open('GetStatus.xml').read()
     response = requests.post('http://localhost:5000/oseo', data=msg,
                              headers={'Content-Type': 'application/xml'})
     response.text
'''

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from celery import Celery

app = Flask(__name__)
app.config.from_object('pyoseo.config')
db = SQLAlchemy(app)
celery_app = Celery('pyoseo')
celery_app.conf.add_defaults(app.config)

from pyoseo import views, models, admin, tasks
