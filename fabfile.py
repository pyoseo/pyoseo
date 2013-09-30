from fabric.api import local

def initial_setup():
    venv_name = 'venv'
    pip_command = '%s/bin/pip' % venv_name
    requirements_file = 'requirements.txt'
    _create_virtualenv(venv_name)
    _local_install_pip_requirements(pip_command, requirements_file)
    _local_download_pyxb(pip_command)
    _local_configure_pyxb_schemas()
    _local_install_pyxb()

def _create_virtualenv(name):
    local('virtualenv %s' % name)

def _local_download_pyxb(pip_command):
    local('%s install --no-install pyxb' % pip_command)

def _local_configure_pyxb_schemas():
    with open('venv/build/pyxb/pyxb/bundles/opengis/scripts/genbind', 'w') as \
            fh:
        pass

def _local_install_pip_requirements(pip_command, requirements):
    local('%s install -r %s' % (pip_command, requirements))

def _local_install_pyxb(pip_command):
    pass
