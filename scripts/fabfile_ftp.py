'''
Install and manage an FTP service with virtual users.

This fabfile will set up the vsftpd server with virtual users, so that it is
ready to be used for delivering orders.

It will:

    * install vsftpd and a pam module for using pwdfiles
    * create the vsftpd configuration file
    * create the pam service file
    * create a new user called vsftpd without login rights
    * set up the /var/www directory to be used as the root for virtual FTP 
      users

NOTE: If this script fails, try running the command

    newgrp www-data

In order to refresh the www-data's group permissions
'''

import os
import datetime as dt
from fabric.api import settings, local

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
VSFTPD_DIR = '/etc/vsftpd'
FTP_SERVICE_ROOT = '/var/www'
PAM_SERVICE_NAME = 'vsftpd.virtual'
PASSWORDS_PATH = os.path.join(VSFTPD_DIR, 'ftpd.passwd')
CHROOT_FILE = os.path.join(VSFTPD_DIR, 'vsftpd.chroot_list')

def install_ftp_service():
    local('sudo apt-get install vsftpd libpam-pwdfile')
    local('sudo chmod a+r %s' % FTP_SERVICE_ROOT)
    local('sudo chmod a+x %s' % FTP_SERVICE_ROOT)
    local('sudo chown --recursive www-data:www-data %s' % FTP_SERVICE_ROOT)
    local('sudo chmod --recursive g+w %s' % FTP_SERVICE_ROOT)
    local('sudo adduser %s www-data' % os.environ['USER'])
    local('sudo chmod g+s %s' % FTP_SERVICE_ROOT)
    if not os.path.isdir(VSFTPD_DIR):
        local('sudo mkdir %s' % VSFTPD_DIR)
        local('sudo chown root:%s %s' % (os.environ['USER'], VSFTPD_DIR))
        local('sudo chmod g+w %s' % VSFTPD_DIR)
    _create_vsftpd_config()
    _create_pam_config()
    _create_vsftpd_system_user()
    _create_password_file('teste', 'teste')
    local('sudo service vsftpd stop')
    local('sudo service vsftpd start')

def _create_vsftpd_system_user():
    user_name = 'vsftpd'
    home_dir = os.path.join('/home', user_name)
    if not os.path.isdir(home_dir):
        local('sudo useradd --home %s --gid nogroup --create-home '
              '--shell /bin/false %s' % (home_dir, user_name))
        local('sudo adduser {} www-data'.format(user_name))

def add_ftp_user(user, password, chroot):
    '''
    Add a new vsftpd virtual user.
    '''

    if not isinstance(chroot, bool):
        if chroot.lower() == 'true':
            chroot = True
        else:
            chroot = False
    _update_password_file(user, password)
    _create_virtual_user_home(user, chroot)

def _create_virtual_user_home(user, chroot):
    user_home = os.path.join(FTP_SERVICE_ROOT, user)
    try:
        os.makedirs(os.path.join(user_home, 'data'))
    except OSError as err:
        if err.errno == 17:
            print('user home already exists')
            pass
        else:
            raise
    local('chmod g-w %s' % user_home)
    local('chmod --recursive 775  %s' % os.path.join(user_home, 'data'))
    if not chroot:
        _update_chroot_list(user)

def _create_pam_config():
    '''
    Create the PAM configuration file for vsftpd.
    '''

    pam_file = '/etc/pam.d/%s' % PAM_SERVICE_NAME
    pam_contents = [
        'auth required pam_pwdfile.so pwdfile %s\n' % PASSWORDS_PATH,
        'account required pam_permit.so\n'
    ]
    with open(os.path.basename(pam_file), 'w') as fh:
        fh.writelines(pam_contents)
    local('sudo mv %s %s' % (os.path.basename(pam_file),
          pam_file))
    local('sudo chown root:root %s' % pam_file)

def _create_vsftpd_config():
    '''
    Create the vsftpd configuration file and place it in the correct path.

    The included configuration directives enable vsftpd virtual hosts.
    '''

    vsftpd_conf_path = '/etc/vsftpd.conf'
    _backup_file(vsftpd_conf_path)
    vsftpd_conf = [
        'listen=YES\n',
        'anonymous_enable=NO\n',
        'local_enable=YES\n',
        'write_enable=YES\n',
        'local_umask=022\n',
        'nopriv_user=vsftpd\n',
        'virtual_use_local_privs=YES\n',
        'guest_enable=YES\n',
        'user_sub_token=$USER\n',
        'local_root=%s/$USER\n' % FTP_SERVICE_ROOT,
        'chroot_local_user=YES\n',
        'chroot_list_enable=YES\n',
        'chroot_list_file=%s\n' % CHROOT_FILE,
        'hide_ids=YES\n',
        'guest_username=vsftpd\n',
        'pam_service_name=%s\n' % PAM_SERVICE_NAME,
        'xferlog_enable=YES\n',
        'xferlog_file=/var/log/vsftpd.log\n',
    ]
    with open(os.path.basename(vsftpd_conf_path), 'w') as fh:
        fh.writelines(vsftpd_conf)
    local('sudo mv %s %s' % (os.path.basename(vsftpd_conf_path),
          vsftpd_conf_path))
    local('sudo chown root:root %s' % vsftpd_conf_path)

def _update_password_file(user, password):
    contents = []
    hashed_password = local('openssl passwd -1 %s' % password, capture=True)
    with open(PASSWORDS_PATH) as fh:
        for line in fh:
            contents.append(line)
    already_present = False
    for count, line in enumerate(contents):
        old_user, old_hashed_pass = line.strip().split(':')
        if old_user == user:
            print('this user is already present in the password file. '
                  'Updating the password...')
            contents[count] = '%s:%s\n' % (user, hashed_password)
            already_present = True
    if not already_present:
        contents.append('%s:%s\n' % (user, hashed_password))
    with open(os.path.basename(PASSWORDS_PATH), 'w') as fh:
        fh.writelines(contents)
    local('mv %s %s' % (os.path.basename(PASSWORDS_PATH), PASSWORDS_PATH))

def _update_chroot_list(user):
    found = False
    contents = []
    with open(CHROOT_FILE) as fh:
        for line in fh:
            contents.append(line)
    for count, line in enumerate(contents):
        old_user = line.strip()
        if old_user == user:
            print('user {} is already exempt from chroot'.format(user))
            found = True
    if not found:
        contents.append('{}\n'.format(user))
        with open(os.path.basename(CHROOT_FILE), 'w') as fh:
                fh.writelines(contents)
        local('mv %s %s' % (os.path.basename(CHROOT_FILE), CHROOT_FILE))

def _create_password_file(first_user, password):
    hashed_password = local('openssl passwd -1 %s' % password, capture=True)
    contents = ['%s:%s\n' % (first_user, hashed_password)]
    with open(os.path.basename(PASSWORDS_PATH),'w') as fh:
        fh.writelines(contents)
    local('mv %s %s' % (os.path.basename(PASSWORDS_PATH), PASSWORDS_PATH))
    # creating an empty chroot_list file, otherwise vsftpd barfs
    local('touch {}'.format(os.path.basename(CHROOT_FILE)))
    local('mv {} {}'.format(os.path.basename(CHROOT_FILE), CHROOT_FILE))
    _create_virtual_user_home(first_user, True)

def _backup_file(path):
    file_name = os.path.basename(path)
    output_path = os.path.join(LOCAL_DIR, file_name)
    now = dt.datetime.utcnow()
    local('cp %s %s.bak.%s' % (path, output_path,
          now.strftime('%Y%m%d%H%M%S')))
