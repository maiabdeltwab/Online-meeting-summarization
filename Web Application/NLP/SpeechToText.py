 # pylint: disable=invalid-name
"""
speech to text model
"""
import os
import uuid

import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence

from MeetApp.settings import MEDIA_ROOT


def speech_to_text(path):
    """ a function that splits the audio file into chunks
        and applies speech recognition
    """
    try:
        # open the audio file stored in
        # the local system as a wav file.
        song = AudioSegment.from_wav(path)

        print("Recognizing...")

        # open a file where we will concatenate
        # and store the recognized text
        # genere a unique file name
        filename = 'STT-' + str(uuid.uuid4()) + '.txt'
        out_path = os.path.join(
            MEDIA_ROOT, 'upload/speech_to_text/' + filename)
        fh = open(out_path, "w+")

        # split track where silence is 0.5 seconds
        # or more and get chunks
        chunks = split_on_silence(song,
                                  # must be silent for at least 0.5 seconds
                                  # or 500 ms. adjust this value based on user
                                  # requirement. if the speaker stays silent for
                                  # longer, increase this value. else, decrease it.
                                  # 280
                                  # 350
                                  # 370
                                  # 390
                                  min_silence_len=800,

                                  # consider it silent if quieter than -16 dBFS
                                  # adjust this per requirement
                                  # -30
                                  # -35
                                  silence_thresh=-37,
                                  keep_silence=160
                                  )

        # create a directory to store the audio chunks.
        path = 'media/upload/audio_chunks'
        try:
            os.mkdir(path)
        except(FileExistsError):
            pass

            # move into the directory to
            # store the audio files.
        os.chdir(path)

        i = 0
        # process each chunk
        for chunk in chunks:

            # Create 0.5 seconds silence chunk
            chunk_silent = AudioSegment.silent(duration=510)

            # add 0.5 sec silence to beginning and
            # end of audio chunk. This is done so that
            # it doesn't seem abruptly sliced.
            audio_chunk = chunk_silent + chunk + chunk_silent

            # export audio chunk and save it in
            # the current directory.
            # specify the bitrate to be 192 k
            audio_chunk.export(
                "./chunk{0}.wav".format(i), bitrate='192k', format="wav")

            # the name of the newly created chunk
            filename = 'chunk'+str(i)+'.wav'

            # create a speech recognition object
            r = sr.Recognizer()

            # recognize the chunk
            with sr.AudioFile(filename) as source:
                audio_listened = r.record(source)

            try:
                # try converting it to text
                rec = r.recognize_google(audio_listened)
                # write the output to the file.
                fh.write(rec+" ")

                # catch any errors.
            except sr.UnknownValueError as e:
                print(e)

            except sr.RequestError as e:
                print("Could not request results. check your internet connection ", e)

            i += 1

            os.remove(filename)  # delete the chunk

        os.chdir('..')
        fh.close()
        print("speech to text ended successfully")

        return out_path

    except: # pylint: disable=bare-except
        print("An exception occurred in speech to text")


#speech_to_text('G:/4th year/Grad. projects/ENGLISH SPEECH.wav')
