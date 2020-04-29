import os
import cv2
import PIL
import pydicom
import numpy as np
from pydicom.filereader import read_dicomdir
from fastai.vision import pil2tensor, Image


def extract_dcm_from_dir(dicomdir_path):
    """
    extract dcm from the dicomdir file. Visit all possible images inside
    the DICOM directory

    input:
    - dicomdir_path: path to dicomdir

    output:
    - a list of dcm from the dicom dir
    """

    input_path, _ = os.path.split(dicomdir_path)
    dicomdir = read_dicomdir(dicomdir_path)

    im_list = []

    # ugly :(
    for patient_record in dicomdir.patient_records:
        for study in patient_record.children:
            for series in study.children:
                for im in series.children:
                    dcm_file = pydicom.dcmread(
                        os.path.join(input_path, *im.ReferencedFileID))
                    im_list.append(dcm_file)

    return im_list


def check_dcm_inversion(dcm_in):
    """
    Check wether the input scan intensities are inverted or not
    based on DICOM information:
    - PresentationLUTShape == 'INVERTED'
    - PhotometricIntepretation = 'MONOCHROME'
    """
    inverted = False

    try:
        print(dcm_in.PresentationLUTShape, end=' ')
        if dcm_in.PresentationLUTShape == 'INVERSE':
            inverted = True
    except:
        pass

    try:
        print(dcm_in.PhotometricInterpretation, end=' ')
        if dcm_in.PhotometricInterpretation == 'MONOCHROME1':
            inverted = True
    except:
        pass

    return inverted


def normalize_scan(im):
    """
    Normalize scan
    """
    return ((im / im.max()) * 255).astype('uint8')


def load_image(image_path):
    """
    Load the input images. `image_path` can be an image, a DICOMDIR
    or a dcm file

    input:
    - image_path: path to image or dcmdir

    output:
    - tensor_images: list of Pytorch tensors ready for inference

    """

    # check if the image is already an image, a DICOMDIR or a DCM file

    dcm = pydicom.dcmread(image_path)

    im = dcm.pixel_array
    im = normalize_scan(im)

    # check intensity inversion
    if check_dcm_inversion(dcm):
        im = ~im

    x = PIL.Image.fromarray(im).convert('RGB')
    return Image(pil2tensor(x, np.float32).div_(255))
