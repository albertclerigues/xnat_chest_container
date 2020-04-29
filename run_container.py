import os
import argparse
from pyxnat import Interface
from lib.preamble import get_preamble
from lib.email_utils import send_email
from lib.image_utils import load_image
from lib.model_utils import initialize_pred_model, initialize_qa_model


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

    # get models
    current_path = os.path.dirname(os.path.abspath(__file__))
    models_path = os.path.join(current_path, 'models')
    covid_model = initialize_pred_model(models_path)
    qa_model = initialize_qa_model(models_path)

    covid_probs = []
    for scan in scan_dicoms:

        # load the input image as a Fastai image class
        im = load_image(scan)

        # check orientation
        # get the probability for the "frontal " class
        prob_qa = qa_model.predict(im)[2][0].numpy()

        if prob_qa > 0.50:
            covid_prob = covid_model.predict(im)[2][0].numpy()
        else:
            covid_prob = -1
        covid_probs.append(covid_prob)

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
                scan = session.select('/projects/{}/subjects/{}/experiments/{}/scans/{}'.format(
                    args.project, args.subject, args.experiment, scan_id))
                scan.attrs.set('xnat:imageScanData/note', 'p(COVID): {0:.2f}%'.format(covid_prob))

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
            body.append('---------------------------------------------------------------')
            body.append('Subject ID: {}'.format(args.subject))
            body.append('DICOM Path: {}'.format(dicom_filepath))
            body.append('Scan ID: {}'.format(scan_id))
            body.append('Predicted Probability: {:.2f}%'.format(covid_prob))
            body.append('---------------------------------------------------------------')

    # send email
    send_email(session, args, body)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract data from XNAT.')
    parser.add_argument('--project', help='XNAT parent project')
    parser.add_argument('--subject', help='XNAT subject')
    parser.add_argument('--experiment', help='XNAT MR session')

    args = parser.parse_args()
    main(args)
