""" Abstract text summarization """

import os
import uuid

from gensim.summarization import keywords, summarize
from MeetApp.settings import MEDIA_ROOT


def text_summarization(stt_file_path):
    """ this method take the speech to text output file path
        ==> apply Abstract text summarization
        ==> return the text summary file path
    """
    try:
         # read the text file
        with open(stt_file_path, 'r') as file:
            sst_text = file.read()

        print("Summarization processing ......")

        # apply summarization
        summary = summarize(sst_text, ratio=0.4)
        print('sucess summary >>>>>>')

        ########## Writing text into file ###########
        filename = 'summary-abstract' + \
            str(uuid.uuid4()) + '.txt'  # genere a unique file name
        out_path = 'upload/text_summarization/' + filename

        path = os.path.join(MEDIA_ROOT, out_path)
        text_file = open(path, "w")
        text_file.writelines(summary)
        text_file.close()

        print("summarization ended successfully")

        return out_path

    except:
        print("An exception occurred in text summarization")

# text_summarization("E:/audio.txt")
