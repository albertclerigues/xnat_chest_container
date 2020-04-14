import argparse
import os
from pyxnat import Interface
from inference.run_inference import run_inference


def main(args):
    xnat_host = os.environ['XNAT_HOST']
    xnat_user = os.environ['XNAT_USER']
    xnat_pass = os.environ['XNAT_PASS']

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
        scan_dicoms += [os.path.join(scan_base, x)
                        for x in os.listdir(scan_base)
                        if x.endswith('.dcm')]  # [0] SELECT ONLY ONE DCM!

    covid_probs = []

    print('--------------------------------------------------')
    print('Inference')

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
    # disconnect the session
    session.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract data from XNAT.')
    parser.add_argument('--project', help='XNAT parent project')
    parser.add_argument('--subject', help='XNAT subject')
    parser.add_argument('--experiment', help='XNAT MR session')

    args = parser.parse_args()
    main(args)
