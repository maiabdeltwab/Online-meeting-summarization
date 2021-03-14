"""
impelement bert extractive text summarization algorithm

"""
import os
import uuid

from summarizer import Summarizer

from MeetApp.settings import MEDIA_ROOT

def text_summarization(stt_file_path):
    """ this method take the speech to text output file path
        ==> apply bert extractive text summarization
        ==> return the text summary file path
    """
    try:
        #Read Data From input File (sumtext.txt)
        inputfile = open(stt_file_path, "r")
        datainput = (inputfile.read())

        print("Summarization processing ......")

        model = Summarizer()
        result = model(datainput, min_length=10)
        output_summary = ''.join(result)

        #Write Data in output File (bert-extractive-summarizer.txt)
        filename = 'summary-bert' + str(uuid.uuid4()) + '.txt' #genere a unique file name
        out_path = 'upload/text_summarization/' + filename
        path = os.path.join(MEDIA_ROOT, out_path)

        file = open(path, "a")
        file.write(output_summary)
        file.close()

        print('sucess summary >>>>>>')

        return out_path
    # pylint: disable=bare-except
    except:
        print("An exception occurred in text summarization")

#text_summarization("C:/Users/Mai-AbdEltwab/Desktop/bert_extractive_summarizer/sumtext.txt")
