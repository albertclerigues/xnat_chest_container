import os
import argparse
from pyxnat import Interface
from lib.preamble import get_preamble
from lib.email_utils import send_email
from COVID19_lib.image_utils import load_image
from COVID19_lib.inference import infer_session_simple
from COVID19_lib.metric_utils import *


def main(args):
    # =====================================================================
    # INFERENCE
    # - Find the ID of each scan as well as the corresponding DICOMS
    # - get model paths
    # - Predict chest view
    # - Predict COVID19 probability on frontal chest scans
    # =====================================================================

    scan_ids, scan_dicoms = os.listdir('/input/SCANS'), []
    for scan_id in scan_ids:
        base = '/input/SCANS/{}/DICOM/'.format(scan_id)
        current_scan_dicoms = [
            os.path.join(base, x) for x in os.listdir(base)
            if x.endswith('.dcm')]

        if len(current_scan_dicoms) > 1:
            current_scan_dicoms = current_scan_dicoms[0]
        scan_dicoms += current_scan_dicoms

    covid_probs = []
    for scan in scan_dicoms:
        im, _ = load_image(scan)
        covid_prob = infer_session_simple(im)[0]
        covid_probs.append(covid_prob)
        print('DEBUG:', scan, 'PROB:', covid_prob)
    # =====================================================================
    # RESULTS
    # - Write note on XNAT scan with the results
    # =====================================================================

    session = Interface(server=os.environ['XNAT_HOST'],
                        user=os.environ['XNAT_USER'],
                        password=os.environ['XNAT_PASS'])

    try:
        for scan_id, dicom_filepath, covid_prob in zip(scan_ids,
                                                       scan_dicoms,
                                                       covid_probs):

            print('--------------------------------------------------')
            print('DICOM PATH', dicom_filepath)
            print("SCAN ID:", scan_id)
            print("predicted probability:", covid_prob)
            print('--------------------------------------------------')

            if covid_prob is not -1:
                scan = session.select(
                    '/projects/{}/subjects/{}/experiments/{}/scans/{}'.format(
                        args.project, args.subject, args.experiment, scan_id))
                scan.attrs.set(
                    'xnat:imageScanData/note', 'p(COVID): {0:.2f}%'.format(
                        covid_prob))

    except Exception as e:
        session.disconnect()
        raise RuntimeError('Error while writting results to XNAT', str(e))

    # ===================================================================
    # EMAIL COMMUNICATION
    # send email to user.
    # - Get the preamble
    # - update the probabilities
    # - send email
    # ===================================================================

    body = get_preamble()
    for scan_id, dicom_filepath, covid_prob in zip(scan_ids,
                                                   scan_dicoms,
                                                   covid_probs):

        if covid_prob is not -1:
            body.append('Diagnostic results:')
            body.append('-------------------------------------------------------------------------')
            body.append('Subject ID: {}'.format(args.subject))
            # body.append('SUBJECT ID: {}'.format(args.subject))
            # body.append('DICOM Path: {}'.format(dicom_filepath))
            body.append('Predicted Probability for COVID-19: {:.2f}%'.format(covid_prob))
            body.append('-------------------------------------------------------------------------')

    # send email
    send_email(session, args, body)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract data from XNAT.')
    parser.add_argument('--project', help='XNAT parent project')
    parser.add_argument('--subject', help='XNAT subject')
    parser.add_argument('--experiment', help='XNAT MR session')

    args = parser.parse_args()
    main(args)
