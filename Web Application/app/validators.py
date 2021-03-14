""" validators of models """

import os
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    """ validtor for uploding voice type """
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.wav', '.mp3']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')
