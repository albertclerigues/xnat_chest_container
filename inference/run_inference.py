import os
import cv2
import numpy as np
import argparse
import subprocess
import PIL
from fastai.vision import load_learner, pil2tensor, Image


def initialize_model(model_name='resnet50_512'):
    """
    Initialize the model from disk
    By default, the model is exported to './export.pkl'

    return the model
    """

    current_path = os.path.dirname(os.path.abspath( __file__ ))

    if model_name == 'resnet50_512':
        model_path = os.path.join(current_path, 'models', 'resnet_512')
    else:
        model_path = os.path.join(current_path, 'models', 'resnet_2stage_224')
    return load_learner(model_path)


def load_image(image_path):
    """
    Load the input image
    """

    # check if the image is already an image or a DCM
    if image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
        im = cv2.imread(image_path)
    else:
        # im = pydicom.dcmread(image_path).pixel_array

        cmd = ['dcmj2pnm', '--write-png', image_path, 'tmp.png']
        subprocess.run(cmd)
        im = cv2.imread('tmp.png')

    # trasnform the image to uint8 rgb
    im = ((im / im.max()) * 255).astype('uint8')
    x = PIL.Image.fromarray(im).convert('RGB')

    # return the fastai image object
    return Image(pil2tensor(x, np.float32).div_(255))


def run_inference(input_scan, model_name='resnet50_512'):

    """
    Run the infered model
    inputs:
    - input_scan: input x-ray image
    - model_name: inferred model used

    output:
    - output probability for COVID
    """

    # load the learner. by default the model is stored in the
    # same folder

    # initialize the model
    learn = initialize_model(model_name=model_name)

    # load the input image as a Fastai image class
    im = load_image(input_scan)

    # predict the probability to pertain to the COVID class
    pred = learn.predict(im)[2][0].numpy()
    print(pred)
    return pred



if __name__ == "__main__":
    """
    COVID-19 x-ray classification
    resnet50 two stage model
    """
    parser = argparse.ArgumentParser(
        description='COVID-19 x-ray classification')
    parser.add_argument('--input_scan', default=None, help='input_image')
    parser.add_argument('--model',
                        default='resnet50_512',
                        help=['Model to use for inference:',
                              'Resnet50_512',
                              'or',
                              'resnet_2stage_224'])
    opt = parser.parse_args()

    prob = run_inference(opt.input_scan, opt.model)

    scan_name = os.path.split(opt.input_scan)[1]

    print('--------------------------------------------------')
    print('SCAN: {0} ----> PROB: {1:.2f} %'.format(scan_name, prob * 100))
    print('--------------------------------------------------')
