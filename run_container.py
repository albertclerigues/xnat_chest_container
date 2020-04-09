import argparse
import pyxnat
import os
import shutil

def main(args):
    xnat_host = os.environ['XNAT_HOST']
    xnat_user = os.environ['XNAT_USER']
    xnat_pass = os.environ['XNAT_PASS']

    
    # Find the ID of each scan as well as the corresponding DICOMS
    scan_ids = os.listdir('/input/SCANS')
    scan_dicoms = []
    for scan_id in scan_ids:
        scan_base = '/input/SCANS/{}/DICOM/'.format(scan_id)
        scan_dicoms += [os.path.join(scan_base, x) for x in os.listdir(scan_base) if x.endswith('.dcm')] #[0] SELECT ONLY ONE DCM!

    # Get one covid probability for each scan_id (deep learning much?)
    covid_probs = [65.0, 50.0]

    # Write results as a note to each scan
    session = pyxnat.Interface(server=xnat_host, user=xnat_user, password=xnat_pass)
    for scan_id, dicom_filepath, covid_prob in zip(scan_ids, scan_dicoms, covid_probs):
        scan = session.select('/projects/{}/subjects/{}/experiments/{}/scans/{}'.format(
            args.project, args.subject, args.experiment, scan_id))
        scan.attrs.set('xnat:imageScanData/note', 'p(COVID) {}% at {}'.format(covid_prob, dicom_filepath))
    session.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract data from XNAT.')
    parser.add_argument('--project', help='XNAT parent project')
    parser.add_argument('--subject', help='XNAT subject')
    parser.add_argument('--experiment', help='XNAT MR session')

    args = parser.parse_args()
    main(args)






