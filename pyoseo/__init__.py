'''
pyoseo, a flask-based OGC OSEO server.

Fire up an ipython shell and type:
    import pyoseo
    pyoseo.db.create_all()
    from mixer.backend.sqlalchemy import mixer
    messages = mixer.cycle().blend('pyoseo.models.User')
    pyoseo.db.session.add_all(messages)
    pyoseo.db.session.commit()
'''

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flaskext.enterprise import Enterprise

app = Flask(__name__)
app.config.from_object('pyoseo.config')
db = SQLAlchemy(app)
enterprise = Enterprise(app)

from pyoseo import views, models, admin
