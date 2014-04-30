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
'''

import os
import datetime as dt
from fabric.api import settings, local

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))

def install_ftp_service():
    local('sudo apt-get install vsftpd libpam-pwdfile')
    vsftpd_dir = '/etc/vsftpd'
    ftp_service_root = '/var/www'
    if not os.path.isdir(vsftpd_dir):
        local('sudo mkdir %s' % vsftpd_dir)
        local('sudo chown root:%s %s' % (os.environ['USER'], vsftpd_dir))
        local('sudo chmod g+w %s' % vsftpd_dir)
    pam_service_name = 'vsftpd.virtual'
    _create_vsftpd_config(ftp_service_root, pam_service_name)
    passwords_path = os.path.join(vsftpd_dir, 'ftpd.passwd')
    _create_pam_config(pam_service_name, passwords_path)
    _create_vsftpd_system_user()
    _create_password_file('teste', 'teste', passwords_path)
    #add_ftp_user('teste', 'teste', passwords_path, ftp_service_root)
    local('sudo chmod a+r %s' % ftp_service_root)
    local('sudo chmod a+x %s' % ftp_service_root)
    local('sudo service vsftpd stop')
    local('sudo service vsftpd start')

def _create_vsftpd_system_user():
    user_name = 'vsftpd'
    home_dir = os.path.join('/home', user_name)
    if not os.path.isdir(home_dir):
        local('sudo useradd --home %s --gid nogroup --create-home '
              '--shell /bin/false %s' % (home_dir, user_name))

# TODO
# * Implement the chroot argument
def add_ftp_user(user, password, password_file, ftp_root, chroot=True):
    '''
    Add a new vsftpd virtual user.
    '''

    _update_password_file(user, password, password_file)
    user_home = os.path.join(ftp_root, user)
    try:
        os.makedirs(os.path.join(user_home, 'data'))
    except OSError as err:
        if err.errno == 17:
            print('user home already exists')
            pass
        else:
            raise
    local('sudo chmod a-w %s' % user_home)
    local('sudo chmod --recursive 755  %s' % os.path.join(user_home, 'data'))
    local('sudo chown --recursive vsftpd:www-data  %s' % user_home)

def _create_pam_config(pam_service_name, ftp_passwords_file):
    '''
    Create the PAM configuration file for vsftpd.
    '''

    pam_file = '/etc/pam.d/%s' % pam_service_name
    pam_contents = [
        'auth required pam_pwdfile.so pwdfile %s\n' % ftp_passwords_file,
        'account required pam_permit.so\n'
    ]
    with open(os.path.basename(pam_file), 'w') as fh:
        fh.writelines(pam_contents)
    local('sudo mv %s %s' % (os.path.basename(pam_file),
          pam_file))
    local('sudo chown root:root %s' % pam_file)

def _create_vsftpd_config(ftp_root_path, pam_service_name):
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
        'local_root=%s/$USER\n' % ftp_root_path,
        'chroot_local_user=YES\n',
        'hide_ids=YES\n',
        'guest_username=vsftpd\n',
        'pam_service_name=%s\n' % pam_service_name,
        'xferlog_enable=YES\n',
        'xferlog_file=/var/log/vsftpd.log\n',
    ]
    with open(os.path.basename(vsftpd_conf_path), 'w') as fh:
        fh.writelines(vsftpd_conf)
    local('sudo mv %s %s' % (os.path.basename(vsftpd_conf_path),
          vsftpd_conf_path))
    local('sudo chown root:root %s' % vsftpd_conf_path)

def _update_password_file(user, password, path):
    contents = []
    hashed_password = local('openssl passwd -1 %s' % password, capture=True)
    with open(path) as fh:
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
    with open(os.path.basename(path), 'w') as fh:
        fh.writelines(contents)
    local('mv %s %s' % (os.path.basename(path), path))

def _create_password_file(first_user, password, path):
    hashed_password = local('openssl passwd -1 %s' % password, capture=True)
    contents = ['%s:%s\n' % (first_user, hashed_password)]
    with open(os.path.basename(path),'w') as fh:
        fh.writelines(contents)
    local('mv %s %s' % (os.path.basename(path), path))

def _backup_file(path):
    file_name = os.path.basename(path)
    output_path = os.path.join(LOCAL_DIR, file_name)
    now = dt.datetime.utcnow()
    local('cp %s %s.bak.%s' % (path, output_path,
          now.strftime('%Y%m%d%H%M%S')))
