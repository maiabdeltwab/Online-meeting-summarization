""" implement speech to text """

import os
import uuid

import nltk
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence

import NLP.speech_to_text.Punctuator as Punctuator
import NLP.speech_to_text.speakerDiarization as speakerDiarization
from MeetApp.settings import MEDIA_ROOT

def silence_based_conversion(path, fp):
    """ a function that splits the audio file into chunks
         and applies speech recognition
    """
	 # open the audio file stored in
	 # the local system as a wav file.
    song = AudioSegment.from_wav(path)

 # split track where silence is 800 milliseconds
    chunks = split_on_silence(song,

                              min_silence_len=800,

                              # consider it silent if quieter than -37 dBFS

                              silence_thresh=-37,
                              keep_silence=160
                              )

# process each chunk
    for chunk in chunks:

        # Create 510 milliseconds silence chunk
        chunk_silent = AudioSegment.silent(duration=510)

	    # add 510 millisec silence to beginning and
	    # end of audio chunk. This is done so that
	    # it doesn't seem abruptly sliced.
        audio_chunk = chunk_silent + chunk + chunk_silent

	   # export audio chunk and save it in
       # the current directory.
	   # specify the bitrate to be 192 k
        filename = "ch_"+path
        audio_chunk.export(filename, bitrate='192k', format="wav")

	    # create a speech recognition object
        recognizer = sr.Recognizer()

	   # recognize the chunk
        with sr.AudioFile(filename) as source:
            audio_listened = recognizer.record(source)

        try:
			# try converting it to text
            rec = recognizer.recognize_google(audio_listened)
	# write the output to the file.
            fp.write(rec+" ")

	# catch any errors.
        except sr.UnknownValueError as exception:
            print(exception)

        except sr.RequestError as exception:
            print("Could not request results. check your internet connection", exception)

        os.remove(filename)


def speech_to_text(audio_path):
    """ apply speech to text algorithm """
    recfilename = 'upload/stt_speakers/'+'recognized-' + \
        str(uuid.uuid4()) + '.txt'  # stt with speaker recognition
    recfilepath = os.path.join(MEDIA_ROOT, recfilename)
    recfile = open(recfilepath, "w+")

    # for text summarization (speach to text only)
    sumfilename = 'upload/speech_to_text/' + \
        'sumtext-' + str(uuid.uuid4()) + '.txt'
    sumfilepath = os.path.join(MEDIA_ROOT, sumfilename)
    sumfile = open(sumfilepath, "w+")

    names = speakerDiarization.main(
        audio_path, embedding_per_second=0.5, overlap_rate=0.4)
    print("diarized successfully")

    nltk.download('punkt')

    for name in names:
        path = name[2:]
        name_split = path[4:-5].split(",")
        start = speakerDiarization.fmtTime(int(name_split[1][1:]))
        end = speakerDiarization.fmtTime(int(name_split[2][1:]))

        processs_path = os.path.join(
            MEDIA_ROOT, 'upload/audio_speakers/' + "processs.txt")
        fp = open(processs_path, "w+")

        directory = os.path.join(MEDIA_ROOT, 'upload/audio_speakers/')
        os.chdir(directory)
        silence_based_conversion(path, fp)
        os.remove(name)
        os.chdir("..")
        fp.close()

        punctext = Punctuator.punctuator(processs_path)
        recfile.write(start+" to " + end + " Speaker" +
                      name_split[0] + ": " + punctext+"\n \n")
        sumfile.write(punctext+"\n \n")

        os.remove(processs_path)

    recfile.close()
    sumfile.close()
    print('\n stt and punctuation ends successfully')

    return sumfilename, recfilename


#speech_to_text("C:/Users/Mai-AbdEltwab/Desktop/Diarization_STT_Punc/voice3.wav")
