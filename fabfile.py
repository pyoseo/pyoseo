'''
This fabric fabfile will automate local installation of dependencies to PyOSEO.

There are some tricky dependencies:

    - pyxb. We are using pyxb to validate the OGC schemas. For that we need to
      configure pyxb with the opengis bundle and enable the OSEO schema.
      This must be done before installation.
'''

import re
import os

from fabric.api import local
from fabric.context_managers import lcd, shell_env

VENV_NAME = 'venv'
REQUIREMENTS_FILE = 'requirements.txt'
LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
LOCAL_PIP = os.path.join(LOCAL_DIR, VENV_NAME, 'bin', 'pip')

def local_initial_setup():
    _local_create_virtualenv()
    _local_install_pip_requirements()
    _local_install_pyxb()

def _local_create_virtualenv():
    global VENV_NAME
    local('virtualenv %s' % VENV_NAME)

def _local_install_pip_requirements():
    global LOCAL_PIP
    global REQUIREMENTS_FILE
    local('%s install -r %s' % (LOCAL_PIP, REQUIREMENTS_FILE))

def _local_install_pyxb():
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
