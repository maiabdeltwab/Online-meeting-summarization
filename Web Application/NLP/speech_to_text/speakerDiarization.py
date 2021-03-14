"""" speaker diarization """

import argparse
import os

import librosa
import numpy as np
from pydub import AudioSegment

from MeetApp.settings import BASE_DIR,MEDIA_ROOT
from NLP.speech_to_text import uisrnn
import NLP.speech_to_text.ghostvlad.model as spkModel
import NLP.speech_to_text.ghostvlad.toolkits as toolkits


# ===========================================
#        Parse the argument
# ===========================================

parser = argparse.ArgumentParser()
# set up training configuration.
parser.add_argument('--gpu', default='', type=str)
trained_file_path = os.path.join(
    BASE_DIR, 'NLP/speech_to_text/ghostvlad/pretrained/weights.h5')
parser.add_argument('--resume', default=trained_file_path, type=str)
parser.add_argument('--data_path', default='4persons', type=str)
# set up network configuration.
parser.add_argument('--net', default='resnet34s',
                    choices=['resnet34s', 'resnet34l'], type=str)
parser.add_argument('--ghost_cluster', default=2, type=int)
parser.add_argument('--vlad_cluster', default=8, type=int)
parser.add_argument('--bottleneck_dim', default=512, type=int)
parser.add_argument('--aggregation_mode', default='gvlad',
                    choices=['avg', 'vlad', 'gvlad'], type=str)
# set up learning rate, training loss and optimizer.
parser.add_argument('--loss', default='softmax',
                    choices=['softmax', 'amsoftmax'], type=str)
parser.add_argument('--test_type', default='normal',
                    choices=['normal', 'hard', 'extend'], type=str)

global args
#args = parser.parse_args()
args = parser.parse_args([])

pretrained_file_path = os.path.join(
    BASE_DIR, 'NLP/speech_to_text/pretrained/saved_model.uisrnn_benchmark')
SAVED_MODEL_NAME = pretrained_file_path


def append2dict(speakerSlice, spk_period):
    key = list(spk_period.keys())[0]
    value = list(spk_period.values())[0]
    timeDict = {}
    timeDict['start'] = int(value[0]+0.5)
    timeDict['stop'] = int(value[1]+0.5)
    if(key in speakerSlice):
        speakerSlice[key].append(timeDict)
    else:
        speakerSlice[key] = [timeDict]

    return speakerSlice


# {'1': [{'start':10, 'stop':20}, {'start':30, 'stop':40}], '2': [{'start':90, 'stop':100}]}
def arrangeResult(labels, time_spec_rate):
    lastLabel = labels[0]
    speakerSlice = {}
    j = 0
    for i, label in enumerate(labels):
        if(label == lastLabel):
            continue
        speakerSlice = append2dict(
            speakerSlice, {lastLabel: (time_spec_rate*j, time_spec_rate*i)})
        j = i
        lastLabel = label
    speakerSlice = append2dict(speakerSlice, {lastLabel: (
        time_spec_rate*j, time_spec_rate*(len(labels)))})
    return speakerSlice


def genMap(intervals):  # interval slices to maptable
    slicelen = [sliced[1]-sliced[0] for sliced in intervals.tolist()]
    mapTable = {}  # vad erased time to origin time, only split points
    idx = 0
    for i, sliced in enumerate(intervals.tolist()):
        mapTable[idx] = sliced[0]
        idx += slicelen[i]
    mapTable[sum(slicelen)] = intervals[-1, -1]

    keys = [k for k, _ in mapTable.items()]
    keys.sort()
    return mapTable, keys


def fmtTime(timeInMillisecond):
    millisecond = timeInMillisecond % 1000
    minute = timeInMillisecond//1000//60
    second = (timeInMillisecond-minute*60*1000)//1000
    time = '{}:{:02d}.{}'.format(minute, second, millisecond)
    return time


def load_wav(vid_path, sr):
    wav, _ = librosa.load(vid_path, sr=sr)
    intervals = librosa.effects.split(wav, top_db=20)
    wav_output = []
    for sliced in intervals:
        wav_output.extend(wav[sliced[0]:sliced[1]])
    return np.array(wav_output), (intervals/sr*1000).astype(int)


def lin_spectogram_from_wav(wav, hop_length, win_length, n_fft=1024):
    linear = librosa.stft(wav, n_fft=n_fft, win_length=win_length,
                          hop_length=hop_length)  # linear spectrogram
    return linear.T


def load_data(path, win_length=400, sr=16000, hop_length=160, n_fft=512, embedding_per_second=0.5, overlap_rate=0.5):
    wav, intervals = load_wav(path, sr=sr)
    linear_spect = lin_spectogram_from_wav(wav, hop_length, win_length, n_fft)
    mag, _ = librosa.magphase(linear_spect)  # magnitude
    mag_T = mag.T
    freq, time = mag_T.shape
    spec_mag = mag_T

    spec_len = sr/hop_length/embedding_per_second
    spec_hop_len = spec_len*(1-overlap_rate)

    cur_slide = 0.0
    utterances_spec = []

    while(True):  # slide window.
        if(cur_slide + spec_len > time):
            break
        spec_mag = mag_T[:, int(cur_slide+0.5): int(cur_slide+spec_len+0.5)]

        # preprocessing, subtract mean, divided by time-wise var
        mu = np.mean(spec_mag, 0, keepdims=True)
        std = np.std(spec_mag, 0, keepdims=True)
        spec_mag = (spec_mag - mu) / (std + 1e-5)
        utterances_spec.append(spec_mag)

        cur_slide += spec_hop_len

    return utterances_spec, intervals


def main(wav_path, embedding_per_second=1.0, overlap_rate=0.5):

    # gpu configuration
    toolkits.initialize_GPU(args)

    params = {'dim': (257, None, 1),
              'nfft': 512,
              'spec_len': 250,
              'win_length': 400,
              'hop_length': 160,
              'n_classes': 5994,
              'sampling_rate': 16000,
              'normalize': True,
              }

    network_eval = spkModel.vggvox_resnet2d_icassp(input_dim=params['dim'],
                                                   num_class=params['n_classes'],
                                                   mode='eval', args=args)
    network_eval.load_weights(args.resume, by_name=True)

    model_args, _, inference_args = uisrnn.parse_arguments()
    model_args.observation_dim = 512
    uisrnnModel = uisrnn.UISRNN(model_args)
    uisrnnModel.load(SAVED_MODEL_NAME)

    specs, intervals = load_data(
        wav_path, embedding_per_second=embedding_per_second, overlap_rate=overlap_rate)
    mapTable, keys = genMap(intervals)

    feats = []
    for spec in specs:
        spec = np.expand_dims(np.expand_dims(spec, 0), -1)
        v = network_eval.predict(spec)
        feats += [v]

    feats = np.array(feats)[:, 0, :].astype(float)  # [splits, embedding dim]
    predicted_label = uisrnnModel.predict(feats, inference_args)

    time_spec_rate = 1000*(1.0/embedding_per_second) * \
        (1.0-overlap_rate)  # speaker embedding every ?ms
    center_duration = int(1000*(1.0/embedding_per_second)//2)
    speakerSlice = arrangeResult(predicted_label, time_spec_rate)

    # get timig of each slot for each speaker
    for spk, timeDicts in speakerSlice.items():    # time map to orgin wav(contains mute)
        for tid, timeDict in enumerate(timeDicts):
            s = 0
            e = 0
            for i, key in enumerate(keys):
                if(s != 0 and e != 0):
                    break
                if(s == 0 and key > timeDict['start']):
                    offset = timeDict['start'] - keys[i-1]
                    s = mapTable[keys[i-1]] + offset
                if(e == 0 and key > timeDict['stop']):
                    offset = timeDict['stop'] - keys[i-1]
                    e = mapTable[keys[i-1]] + offset

            speakerSlice[spk][tid]['start'] = s
            speakerSlice[spk][tid]['stop'] = e

    # get number of speakers in audio
    num_of_speakers = 0
    for spk in speakerSlice.items():
        num_of_speakers += 1

    # define list for speakers with their start and end time of speaking
    speakers = [[] for x in range(num_of_speakers)]
    count = 0

    for spk, timeDicts in speakerSlice.items():
        for timeDict in timeDicts:
            s = timeDict['start']
            e = timeDict['stop']

            speakers[count].append([spk, s, e])

        count = count + 1

    # get audio
    audio = AudioSegment.from_wav(wav_path)

    # list for names of audios generated after splitting in order
    files_names = []

    # create "audio_speakers" folder to save split audios in it
    directory = os.path.join(MEDIA_ROOT, 'upload/audio_speakers')
    # try:
    #     os.mkdir(directory)
    # except(FileExistsError):
    #     pass

    # move into the directory to
    # store the audio files.
    os.chdir(directory)

    # get the number of total generated audios after splitting
    iterations = 0
    for s in range(len(speakers)):
        for clip in range(len(speakers[s])):
            iterations = iterations + 1

    # split first slot of first speaker and export it as new audio in folder
    start_time = speakers[0][0][1]
    end_time = speakers[0][0][2]
    filename = "./spk{0}.wav".format(speakers[0][0])
    files_names.append(filename)
    new_audio = audio[start_time: end_time]
    new_audio.export(filename, format="wav")

    # split remaining slots in audio in order and export as new audio un folder
    # add the recently split audio names to the files_names list
    for it in range(iterations):
        for i in range(len(speakers)):
            chuncks = speakers[i]
            for j in range(len(chuncks)):
                if (chuncks[j][1] == end_time):
                    start_time = chuncks[j][1]
                    end_time = chuncks[j][2]
                    filename = "./spk{0}.wav".format(chuncks[j])
                    files_names.append(filename)
                    new_audio = audio[start_time: end_time+600]
                    new_audio.export(filename, format="wav")
                    break

    # go up one step in path directory
    os.chdir("..")

    # return the files_names list
    return files_names
