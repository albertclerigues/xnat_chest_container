import os
from fastai.vision import load_learner


def initialize_pred_model(models_path):
    """
    Initialize the model from disk
    By default, the model is exported to './export.pkl'

    input:
    - models_path: path to models

    output:
    - model: fastai model
    """
    return load_learner(os.path.join(models_path, 'covid19'))


def initialize_qa_model(models_path):
    """
    Initialize the quality check model
    By default, the model is exported to 'models/qa/export.pkl'

    input:
    - models_path: path to models

    output:
    - model: fastai model
    """

    return load_learner(os.path.join(models_path, 'qa'))
