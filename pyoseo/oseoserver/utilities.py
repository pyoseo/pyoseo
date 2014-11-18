# Copyright 2014 Ricardo Garcia Silva
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Some utility functions for pyoseo
"""

import importlib
import smtplib
from email.mime.text import MIMEText

from django.conf import settings

def import_class(python_path, *instance_args, **instance_kwargs):
    """
    """

    module_path, sep, class_name = python_path.rpartition('.')
    the_module = importlib.import_module(module_path)
    the_class = getattr(the_module, class_name)
    instance = the_class(*instance_args, **instance_kwargs)
    return instance

def send_mail_to_admins(message):
    """
    """

    mail_domain = settings.OSEOSERVER_MAIL_DOMAIN
    sender_user = settings.OSEOSERVER_MAIL_ACCOUNT
    mail_sender = '{}@{}'.format(sender_user, mail_domain)
    mail_sender_password = settings.OSEOSERVER_MAIL_ACCOUNT_PASSWORD
    sender_server = settings.OSEOSERVER_MAIL_SERVER
    mail_server = '{}.{}'.format(sender_server, mail_domain)
    mail_server_port = settings.OSEOSERVER_MAIL_SERVER_PORT
    mailing_list = settings.OSEOSERVER_ADMIN_MAILS
    msg = MIMEText(message)
    msg['Subject'] = 'pyoseo error'
    msg['From'] = mail_sender
    msg['To'] = ', '.join(mailing_list)
    #print('message: {}'.format(msg))
    #print('mail_server: {}'.format(mail_server))
    #print('mail_server_port: {}'.format(mail_server_port))
    s = smtplib.SMTP(mail_server, mail_server_port)
    s.starttls()
    s.login(sender_user, mail_sender_password)
    s.sendmail(mail_sender, mailing_list, msg.as_string())
    s.quit()
