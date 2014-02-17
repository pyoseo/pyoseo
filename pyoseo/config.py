import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'sqlite.db')
SQLALCHEMY_MIGRATE_REPO = 'sqlite:///' + os.path.join(basedir, 'db_repository')
LOGGER_NAME = 'pyoseo'

