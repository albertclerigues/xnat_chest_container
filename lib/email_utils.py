import os
from email.mime.text import MIMEText
import smtplib
import json


def get_user_credentials():
    """
    get user credentials from secret file
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, 'secret.json')) as json_file:
        data = json.load(json_file)

    return data['id']


def send_email(session, args, body):
    """
    Send an email to user.

    Inputs:
    - session: Xnat session
    - args: container arguments
    - body: email body
    """

    # Get the actual username and email (XNAT_USER is a token alias)

    try:
        # Get actual username from session token
        # admin if launched automatically
        username_token = session.get('/data/services/tokens/validate/{}/{}'.format(
            os.environ['XNAT_USER'],
            os.environ['XNAT_PASS'])).json()['valid']

        # Get actual username from user that uploaded experiment
        username_upload = session.select('/projects/{}/subjects/{}/experiments/{}'.format(
            args.project,
            args.subject,
            args.experiment)).attrs.get('insert_user')

        # Preferably use token username (containers can be run by people other
        # than uploader. If token username is admin, container may be
        # automatically launched (so get uploader)
        if username_token != 'admin':
            username = username_token
        else:
            username = username_upload

        # Then get user email to send results
        users_email = session.manage.users.email(username)

    except Exception as e:
        session.disconnect()
        raise RuntimeError('Error while getting user email', str(e))
    session.disconnect()  # Interaction with XNAT server is finished

    # EMAIL sending

    id_ = get_user_credentials()
    gmail_email = id_['user']
    gmail_password = id_['pass']

    email_text = MIMEText('\n'.join(body))
    email_text['From'] = gmail_email
    email_text['To'] = users_email
    email_text['Subject'] = 'XNAT VICOROB - COVID-19 probability results'

    print('-' * 40 + 'Sending mail:' + '-' * 40)
    print(email_text.as_string())
    print('-' * 40)

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_email, gmail_password)
    server.sendmail(gmail_email, users_email, email_text.as_string())
    server.close()
