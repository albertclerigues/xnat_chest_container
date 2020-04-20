import argparse

from email.mime.text import MIMEText
import smtplib

import os
from pyxnat import Interface
from inference.run_inference import run_inference


def main(args):
    xnat_host = os.environ['XNAT_HOST']
    xnat_user = os.environ['XNAT_USER']
    xnat_pass = os.environ['XNAT_PASS']

    print(os.environ)

    # define model to used
    model = 'resnet50_512'

    # print some loggin information
    print('--------------------------------------------------')
    print('model name:', model)
    print('--------------------------------------------------')
    print(' ')

    # Find the ID of each scan as well as the corresponding DICOMS
    scan_ids = os.listdir('/input/SCANS')

    scan_dicoms = []
    for scan_id in scan_ids:
        scan_base = '/input/SCANS/{}/DICOM/'.format(scan_id)
        current_scan_dicoms = [os.path.join(scan_base, x)
                        for x in os.listdir(scan_base)
                        if x.endswith('.dcm')]  # [0] SELECT ONLY ONE DCM!
        if len(current_scan_dicoms) > 1:
            current_scan_dicoms = current_scan_dicoms[0]

        scan_dicoms += current_scan_dicoms


    print('--------------------------------------------------')
    print('Inference')
    covid_probs = []
    for scan in scan_dicoms:
        # perform inference
        prob = run_inference(scan)
        covid_probs.append(prob)
    print('--------------------------------------------------')

    # Write results as a note to each scan
    session = Interface(server=xnat_host,
                        user=xnat_user,
                        password=xnat_pass)

    for scan_id, dicom_filepath, covid_prob in zip(scan_ids,
                                                   scan_dicoms,
                                                   covid_probs):
        print('--------------------------------------------------')
        scan = session.select('/projects/{}/subjects/{}/experiments/{}/scans/{}'.format(
            args.project, args.subject, args.experiment, scan_id))
        scan.attrs.set('xnat:imageScanData/note',
                       'p(COVID): {0:.2f}%'.format(covid_prob))
        print('DICOM PATH', dicom_filepath)
        print("SCAN ID:", scan_id)
        print("predicted probability:", covid_prob)
        print('--------------------------------------------------')

    # Get the actual username (XNAT_USER is a token alias)
    # Then get user email to send results
    username = session.get('/data/services/tokens/validate/{}/{}'.format(
        os.environ['XNAT_USER'], os.environ['XNAT_PASS'])).json()['valid']
    users_email = session.manage.users.email(username)

    body = []
    for scan_id, dicom_filepath, covid_prob in zip(scan_ids, scan_dicoms, covid_probs):
        body.append('--------------------------------------------------')
        body.append('Subject ID: {}'.format(args.subject))
        body.append('DICOM Path: {}'.format(dicom_filepath))
        body.append('Scan ID: {}'.format(scan_id))
        body.append('Predicted Probability: {:.2f}%'.format(covid_prob))
        body.append('--------------------------------------------------')
    body = '\n'.join(body)

    gmail_email = ''
    gmail_password = ''
    raise NotImplementedError('Please use your own gmail email and password :D')

    email_text = MIMEText(body)
    email_text['From'] = gmail_email
    email_text['To'] = users_email
    email_text['Subject'] = 'XNAT VICOROB - DEBUG! - COVID-19 probability results'

    print('-' * 40 + 'Sending mail:' + '-' * 40)
    print(email_text.as_string())
    print('-' * 40)

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_email, gmail_password)
    server.sendmail(gmail_email, users_email, email_text.as_string())

    # disconnect XNAT and email sessions
    session.disconnect()
    server.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract data from XNAT.')
    parser.add_argument('--project', help='XNAT parent project')
    parser.add_argument('--subject', help='XNAT subject')
    parser.add_argument('--experiment', help='XNAT MR session')

    args = parser.parse_args()
    main(args)
