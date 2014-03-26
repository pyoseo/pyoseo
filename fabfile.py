'''
This fabric fabfile will automate local installation of dependencies to PyOSEO.

There are some tricky dependencies:

    - pyxb. We are using pyxb to validate the OGC schemas. For that we need to
      configure pyxb with the opengis bundle and enable the OSEO schema.
      This must be done before installation.
'''

# TODO
# * get django's secret key out of the repository and use a new one
# * follow the remaining items on the django deployment checklist
# * include some sample configuration for Apache
# * remove giosystemcore from the requirements file. It should be installed
#   manually by a previous process. Alternatively, assume that this fabfile
#   is aimed exclusively at giosystem's usage of pyoseo, move it out of the
#   main pyoseo repository. Then turn the oseoserver app into a standalone
#   django app, create a new django project just for giosystem, add the
#   needed django apps to it, including the oseoserver app and provide it
#   with a fabfile to include giosystemcore as a dependency.
# * Turning oseoserver into a proper django app is the preferred option,
#   as it will also provide a chance to cleanly separate other files (like
#   the celery tasks) from what is giosystem specific functionality and
#   what is related to the OSEO service.

import re
import os
import socket

from fabric.api import local
from fabric.context_managers import lcd, shell_env

VENV_NAME = 'venv'
REQUIREMENTS_FILE = 'requirements.txt'
LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
LOCAL_PIP = os.path.join(LOCAL_DIR, VENV_NAME, 'bin', 'pip')
LOCAL_PYTHON = os.path.join(LOCAL_DIR, VENV_NAME, 'bin', 'python')

DJANGO_PROJECT_NAME = 'pyoseo'
RELATIVE_URL = '/giosystem/orders'
LOCAL_DOMAIN = 'meteo.pt'

def initial_setup(debug=False):
    local('sudo apt-get install rabbitmq-server')
    local('virtualenv %s' % VENV_NAME)
    local('%s install -r %s' % (LOCAL_PIP, REQUIREMENTS_FILE))
    create_local_django_settings(debug)
    with lcd(DJANGO_PROJECT_NAME):
        local('%s manage.py collectstatic --noinput --verbosity=0' %
              LOCAL_PYTHON)
    create_database()
    install_pyxb()

def create_local_django_settings(use_debug):
    '''
    :arg use_debug: Wether to set the DEBUG Django option to True or False
    :type use_debug: str
    '''

    path = os.path.join(LOCAL_DIR, DJANGO_PROJECT_NAME, DJANGO_PROJECT_NAME,
                        'settings_local.py')
    contents = [
        'DEBUG = %s\n' % use_debug,
        'STATIC_URL = \'%s/static/\'\n' % RELATIVE_URL,
    ]
    if str(use_debug) == 'False':
        host_name = '.' + '.'.join((socket.gethostname(), LOCAL_DOMAIN))
        contents.append('ALLOWED_HOSTS = [\'%s\',]' % host_name)
    with open(path, 'w') as fh:
        fh.writelines(contents)

def create_database():
    with lcd(DJANGO_PROJECT_NAME):
        local('%s manage.py syncdb' % LOCAL_PYTHON)
        local('%s manage.py loaddata oseoserver/fixtures/default_data.json' % 
              LOCAL_PYTHON)

def install_pyxb():
    global VENV_NAME
    global LOCAL_PIP
    global LOCAL_DIR
    pyxb_location = 'pyxb'
    #pyxb_location = 'git+http://git.code.sf.net/p/pyxb/code#egg=pyxb'
    local('%s install --no-install %s' % (LOCAL_PIP, pyxb_location))
    build_dir = os.path.join(LOCAL_DIR, VENV_NAME, 'build', 'pyxb')
    with lcd(build_dir):
        genbind_path = '%s/pyxb/bundles/opengis/scripts/genbind' % build_dir
        pattern = re.compile(r'^\$\{SCHEMA_DIR\}')
        new_contents = []
        section_started = False
        with open(genbind_path) as fh:
            for line in fh:
                if pattern.search(line) is not None:
                    if not section_started:
                        section_started = True
                else:
                    if section_started:
                        # add the new line to the end of the section
                        new_lines = [
                            '${SCHEMA_DIR}/oseo/1.0/oseo.xsd oseo\n',
                            '${SCHEMA_DIR}/wps/1.0.0/wpsAll.xsd wps\n',
                        ]
                        new_contents.extend(new_lines)
                        section_started = False
                new_contents.append(line)
        with open(genbind_path, 'w') as fh:
            fh.writelines(new_contents)
        local('chmod 755 %s/scripts/pyxbgen' % build_dir)
        local('chmod 755 %s' % genbind_path)
        with shell_env(PYXB_ROOT=build_dir):
            local(genbind_path)
            local('%s install --no-download pyxb' % LOCAL_PIP)
