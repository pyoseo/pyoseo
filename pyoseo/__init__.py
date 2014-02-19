'''
pyoseo, a flask-based OGC OSEO server.

Fire up an ipython shell and type:

import pyoseo
pyoseo.db.create_all()
from mixer.backend.sqlalchemy import mixer
messages = mixer.cycle().blend('pyoseo.models.User')
pyoseo.db.session.add_all(messages)
pyoseo.db.session.commit()

To get the test server running, execute the runserver.py script

    $ python runserver.py

To test the server, cd to the samples directory and send some requests
using curl:

    $ curl --include --header "Content-Type: application/xml" \
            --data @GetStatus.xml http://localhost:5000/oseo

Alternatively you can test in python, using the requests library:

    import requests
    msg = open('GetStatus.xml').read()
    response = requests.post('http://localhost:5000/oseo', data=msg,
                             headers={'Content-Type': 'application/xml'})
    response.text
'''

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('pyoseo.config')
db = SQLAlchemy(app)

from pyoseo import views, models, admin
