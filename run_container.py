import argparse
from email.mime.text import MIMEText
import smtplib
import os
from pyxnat import Interface
from inference.run_inference import run_inference


def main(args):
    # =====================================================================
    # INFERENCE
    # =====================================================================

    # define model to used
    model = 'resnet50_512'
    print('model name:', model) # print some loggin information

    # Find the ID of each scan as well as the corresponding DICOMS
    scan_ids, scan_dicoms = os.listdir('/input/SCANS'), []
    for scan_id in scan_ids:
        base = '/input/SCANS/{}/DICOM/'.format(scan_id)
        current_scan_dicoms = [
            os.path.join(base, x) for x in os.listdir(base) if x.endswith('.dcm')]  
        if len(current_scan_dicoms) > 1:
            current_scan_dicoms = current_scan_dicoms[0]
        scan_dicoms += current_scan_dicoms
    
    print('Performing inference...')
    covid_probs = [run_inference(scan) for scan in scan_dicoms]

    # =====================================================================
    # RESULTS
    # =====================================================================

    #### Send results to appropiate places
    session = Interface(server=os.environ['XNAT_HOST'], 
        user=os.environ['XNAT_USER'], password=os.environ['XNAT_PASS'])

    # ---------------------------------------------------------------------
    # Write note on XNAT scan with the results
    # ---------------------------------------------------------------------
    try:
        for scan_id, dicom_filepath, covid_prob in zip(scan_ids, scan_dicoms, covid_probs):
            scan = session.select('/projects/{}/subjects/{}/experiments/{}/scans/{}'.format(
                args.project, args.subject, args.experiment, scan_id))
            scan.attrs.set('xnat:imageScanData/note', 'p(COVID): {0:.2f}%'.format(covid_prob))

            print('--------------------------------------------------')
            print('DICOM PATH', dicom_filepath)
            print("SCAN ID:", scan_id)
            print("predicted probability:", covid_prob)
            print('--------------------------------------------------')
    except Exception as e:
        session.disconnect()
        raise RuntimeError('Error while writting results to XNAT', str(e))

    # ---------------------------------------------------------------------
    # Send an email with results to user
    # ---------------------------------------------------------------------
    
    #### Get the actual username and email (XNAT_USER is a token alias)
    try:
        # Get actual username from session token (admin if launched automatically)
        username_token = session.get('/data/services/tokens/validate/{}/{}'.format(
            os.environ['XNAT_USER'], os.environ['XNAT_PASS'])).json()['valid']
        # Get actual username from user that uploaded experiment
        username_upload = session.select('/projects/{}/subjects/{}/experiments/{}'.format(
            args.project, args.subject, args.experiment)).attrs.get('insert_user')
        # Preferably use token username (containers can be run by people other than uploader)
        # If token username is admin, container may be automatically launched (so get uploader)
        if username_token != 'admin': username = username_token
        else: username = username_upload
        # Then get user email to send results    
        users_email = session.manage.users.email(username)
    except Exception as e:
        session.disconnect()
        raise RuntimeError('Error while getting user email', str(e))
    session.disconnect() # Interaction with XNAT server is finished

    #### EMAIL sending
    gmail_email = 'albertclerigues@gmail.com'
    gmail_password = 'tqqvgothdjdjppxn'

    body = []
    for scan_id, dicom_filepath, covid_prob in zip(scan_ids, scan_dicoms, covid_probs):
        body.append('---------------------------------------------------------------')
        body.append('Subject ID: {}'.format(args.subject))
        body.append('DICOM Path: {}'.format(dicom_filepath))
        body.append('Scan ID: {}'.format(scan_id))
        body.append('Predicted Probability: {:.2f}%'.format(covid_prob))
        body.append('---------------------------------------------------------------')
    email_text = MIMEText('\n'.join(body))
    email_text['From'] = gmail_email
    email_text['To'] = users_email
    email_text['Subject'] = 'XNAT VICOROB - [DEBUG] - COVID-19 probability results'

    print('-' * 40 + 'Sending mail:' + '-' * 40)
    print(email_text.as_string())
    print('-' * 40)

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_email, gmail_password)
    server.sendmail(gmail_email, users_email, email_text.as_string())
    server.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract data from XNAT.')
    parser.add_argument('--project', help='XNAT parent project')
    parser.add_argument('--subject', help='XNAT subject')
    parser.add_argument('--experiment', help='XNAT MR session')

    args = parser.parse_args()
    main(args)
