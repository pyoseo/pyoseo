'''
A script for setting pyoseo up in the apache webserver as part of the giosystem
framework
'''

import os
import sys
import getpass
import argparse
import subprocess
import socket
import datetime as dt
import shutil
import inspect

def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('project_root', help='Root directory for this project')
    parser.add_argument('-a', '--server_admin_email', help='email address '
                        'of the web server\'s administrator',
                        default='gio@ipma.pt')
    return parser

def main():
    project_name = 'pyoseo'
    parser = build_parser()
    args = parser.parse_args()
    project_root = os.path.abspath(args.project_root)
    configure_server()
    configure_site(args.server_admin_email, project_root, project_name)

def configure_server():
    '''
    Configure general settings of the web server
    '''
    new_contents = []
    conf_name = 'apache2.conf'
    conf_dir = '/etc/apache2'
    backup_configuration_file(os.path.join(conf_dir, conf_name))
    with open(os.path.join(conf_dir, conf_name)) as fh:
        has_server_name = False
        for line in fh:
            if line.startswith('ServerName'):
                has_server_name = True
            new_contents.append(line)
    if not has_server_name:
        new_contents.append('ServerName localhost\n')
    with open(conf_name, 'w') as fh:
        fh.writelines(new_contents)
    return_code = subprocess.call(['sudo', 'mv', '--force', conf_name,
                                  conf_dir])

def configure_site(server_admin, project_root, project_name):
    '''
    Configure the site
    '''

    site_dir = '/etc/apache2/sites-available'
    conf_file = 'giosystem.conf'
    if not os.path.isfile(os.path.join(site_dir, conf_file)):
        domain_name = subprocess.check_output(['domainname']).strip()
        host_name = socket.gethostname()
        if domain_name != '(none)':
            server_name = '.'.join((host_name, domain_name))
        else:
            server_name = host_name
        contents = create_general_site_conf(server_admin, server_name,
                                            project_root, project_name)
        with open(conf_file, 'w') as fh:
            fh.write(contents)
        return_code = subprocess.call(['sudo', 'mv', '--force', 
                                      conf_file, site_dir])
    else:
        with open(os.path.join(site_dir, conf_file)) as fh:
            old_contents = fh.readlines()
        found_config = False
        for line in old_contents:
            if project_name in line:
                found_config = True
        if not found_config:
            site_config = create_site_specific_conf(project_root, project_name)
            contents = ''.join(old_contents[:-1]) + site_config + \
                       old_contents[-1]
            with open(conf_file, 'w') as fh:
                fh.write(contents)
            return_code = subprocess.call(['sudo', 'mv', '--force', conf_file,
                                          site_dir])

def create_general_site_conf(server_admin, server_name, project_root,
                             project_name):
    tab = 4 * ' '
    contents = '<VirtualHost *:80>\n'
    contents += '{}ServerAdmin {}\n'.format(tab, server_admin)
    contents += '{}ServerName {}\n'.format(tab, server_name)
    contents += '{}ServerAlias localhost\n'.format(tab)
    contents += '{}DocumentRoot /var/www\n\n'.format(tab)
    contents += create_site_specific_conf(project_root, project_name)
    contents += '</VirtualHost>\n'
    return contents

def create_site_specific_conf(project_root, project_name):
    user = getpass.getuser()
    group = user
    num_processes = 1
    num_threads = 1
    python_version = '{}.{}'.format(sys.version_info.major,
                                    sys.version_info.minor)
    venv_dir = os.path.realpath(sys.executable).rsplit('/', 2)[0]
    python_paths = [
        os.path.join(venv_dir, 'lib/python{}/site-packages'.format(
                     python_version)),
        #project_root,
    ]
    path = ':'.join(python_paths)
    relative_url = '/giosystem/processing/wps'
    tab = 4 * ' '
    conf = '{}# {} app configuration\n'.format(tab, project_name)
    conf += '{}WSGIDaemonProcess {} user={} group={} processes={} ' \
            'threads={} display-name=\'%%{{GROUP}}\' python-path={}\n'.format(
                tab, project_name, user, group, num_processes,
                num_threads, path
            )
    conf += '{}WSGIProcessGroup {}\n'.format(tab, project_name)
    conf += '{}WSGIScriptAlias {} {}\n\n'.format(tab, relative_url,
                                                 os.path.join(project_root,
                                                 'wsgi.py'))
    conf += '{}<Location {}>\n'.format(tab, relative_url)
    conf += '{}WSGIProcessGroup {}\n'.format(2*tab, project_name)
    conf += '{}</Location>\n\n'.format(tab)
    conf += '{}<Directory {}>\n'.format(tab, project_root)
    conf += '{}<Files wsgi.py>\n'.format(2*tab)
    conf += '{}Order deny,allow\n'.format(3*tab)
    conf += '{}Allow from all\n'.format(3*tab)
    conf += '{}Require all granted\n'.format(2*tab)
    conf += '{}</Files>\n'.format(2*tab)
    conf += '{}</Directory>\n\n'.format(tab)
    return conf

def backup_configuration_file(conf_path):
    now = dt.datetime.utcnow()
    backup_dir = os.path.expanduser('~/giosystem_backups')
    if not os.path.isdir(backup_dir):
        os.mkdir(backup_dir)
    name = os.path.basename(conf_path)
    new_name = '.'.join((name, now.strftime('%Y%m%d%H%M')))
    shutil.copy(conf_path, os.path.join(backup_dir, new_name))


if __name__ == '__main__':
    main()
