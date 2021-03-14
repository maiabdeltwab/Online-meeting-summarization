""" NLP text punctuator"""

import json
import os
import re
import time
import uuid

import nltk
import numpy as np
import torch
from nltk.tokenize import sent_tokenize
from pytorch_pretrained_bert import BertForMaskedLM, BertTokenizer
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from MeetApp.settings import BASE_DIR, MEDIA_ROOT


def punctuator(path):
    """" this method take the speech to text file path
         ===> apply panctuation algorithm
         ===> return punctuated file path
    """
    nltk.download('punkt')

    '''
    set torch device GPU -if CUDA exists- or CPU
    '''
    # If there's a GPU available...
    if torch.cuda.is_available():

        # Tell PyTorch to use the GPU.
        device = torch.device("cuda")

    # If not...
    else:

        # Tell PyTorch to use the CPU.
        device = torch.device("cpu")

    # set number of samples worked on before updating internal model parameters
    # it is known as batch size
    batch_size = 1024

    # set the tokenizer to that of bert-base-uncased pretrained model
    tokenizer = BertTokenizer.from_pretrained(
        'bert-base-uncased', do_lower_case=True)

    # read hyperparameters of the neural network model
    json_path = os.path.join(BASE_DIR, 'NLP/Punctuation')
    json_path = os.path.join(json_path, 'hyperparameters.json')
    with open(json_path, 'r') as f:
        hyperparameters = json.load(f)
    hyperparameters

    # dictionary for the punctuation marks
    punctuation_enc = {
        'O': 0,
        'COMMA': 1,
        'PERIOD': 2,
        'QUESTION': 3
    }

    segment_size = hyperparameters['segment_size']

    # function to load data from file
    def load_file(filename):
        with open(filename, 'r', encoding="utf8", errors="ignore") as f:  # , encoding='utf-8'
            data = f.readlines()
        return data

    # load text from input file into variable data_test
    data_test = load_file(path)

    '''
    apply tokenization for each line in input text and give ID for each token in line
    save IDs in list
    '''
    X = []
    for line in data_test:
        # word = line.split()
        # print(word)
        tokens = tokenizer.tokenize(line)
        x = tokenizer.convert_tokens_to_ids(tokens)
        if len(x) > 0:
            X += x

    def insert_target(x, segment_size):

        X = []
        x_pad = x[-((segment_size-1)//2-1):]+x+x[:segment_size//2]

        for i in range(len(x_pad)-segment_size+2):
            segment = x_pad[i:i+segment_size-1]
            segment.insert((segment_size-1)//2, 0)
            X.append(segment)

        return np.array(X)

    # class representing the model
    class BertPunc(nn.Module):

        def __init__(self, segment_size, output_size, dropout):
            super(BertPunc, self).__init__()
            self.bert = BertForMaskedLM.from_pretrained('bert-base-uncased')
            self.bert_vocab_size = 30522
            self.bn = nn.BatchNorm1d(segment_size*self.bert_vocab_size)
            self.fc = nn.Linear(segment_size*self.bert_vocab_size, output_size)
            self.dropout = nn.Dropout(dropout)

        def forward(self, x):
            x = self.bert(x)
            x = x.view(x.shape[0], -1)
            x = self.fc(self.dropout(self.bn(x)))

            return x
    #end model

    X_zero_halfway = insert_target(x, segment_size)

    # convert input data into tensor form
    data_set = TensorDataset(torch.from_numpy(X_zero_halfway).long())

    '''
    loading data into memory using PyTorch DataLoader
    Dataloader parallelizes the data loading process with the support of automatic batching 
    '''
    data_loader = DataLoader(data_set, batch_size, shuffle=False)
    output_size = len(punctuation_enc)
    dropout = hyperparameters['dropout']

    # load the pretrained model and set the hardware accelerator to be CPU
    model_path = os.path.join(BASE_DIR, 'NLP/Punctuation')
    model_path = os.path.join(model_path, 'model')
    bert_punc = nn.DataParallel(
        BertPunc(segment_size, output_size, dropout).cpu())
    bert_punc.load_state_dict(torch.load(
        model_path, map_location=torch.device('cpu')))
    bert_punc.eval()

    # set start time to process input in pretrained model
    start_time = time.time()

    # loop  to apply pretrained model on input data
    # save output in list pred
    pred = []
    for inputs in tqdm(data_loader):
        with torch.no_grad():
            inputs = inputs[0].cpu()
            output = bert_punc(inputs)
            pred += list(output.argmax(dim=1).cpu().data.numpy().flatten())
    elapsed_time = time.time() - start_time

    # variables declarations
    restored_text = []
    tokens_for_loop = tokens
    transformed_pred = [None] * len(tokens_for_loop)
    words_with_punctuation = [None] * len(tokens_for_loop)
    restored_text_with_masks = [None] * len(tokens_for_loop)
    masking = 0

    for i in range(len(tokens_for_loop)):

        # convert to punctuation characters
        if pred[i] == punctuation_enc['COMMA']:
            transformed_pred[i] = ","
        elif pred[i] == punctuation_enc['PERIOD']:
            transformed_pred[i] = "."
        elif pred[i] == punctuation_enc['QUESTION']:
            transformed_pred[i] = "?"
        else:
            transformed_pred[i] = ""

      # concatinate words with punctuation characters
        words_with_punctuation[i] = tokens_for_loop[i] + transformed_pred[i]

    words_with_punctuation.extend(['#', '#'])

    for i in range(len(words_with_punctuation)-2):
        #if i < len(words_with_punctuation)-3:

        # delete masks and concatinate masks words
        if re.findall("#{2}", words_with_punctuation[i+1]):

            restored_text_with_masks[i] = words_with_punctuation[i] + \
                words_with_punctuation[i+1].replace('##', '')
            #del words_with_punctuation[i+1]
            if re.findall("#{2}", words_with_punctuation[i+2]):

                restored_text_with_masks[i] = restored_text_with_masks[i] + \
                    words_with_punctuation[i+2].replace('##', '')
                #del words_with_punctuation[i+1]

        else:
            restored_text_with_masks[i] = words_with_punctuation[i]

    restored_text_with_masks_for_loop = restored_text_with_masks

    # loop to restore text after removing masks
    restored_text_without_masks = []
    for i in range(len(restored_text_with_masks_for_loop)):
        if re.findall("#", restored_text_with_masks_for_loop[i]) != ['#', '#']:
            restored_text_without_masks.append(
                restored_text_with_masks_for_loop[i])

    text_not_capitalize = " ".join(restored_text_without_masks).replace(
        " ' ", "'").replace(" - ", "-")

    # apply sent_tokenize on text to produce sentences
    sentences = sent_tokenize(text_not_capitalize)

    # captalize first letter in each sentence in text
    sentences = [sent+"\n" for sent in sentences]
    text = ''.join(sentences)

    # open text file and write the punctuated text
    # genere a unique file name
    filename = 'Pucntuated-' + str(uuid.uuid4()) + '.txt'
    out_path = 'upload/punctuated_text/' + filename

    path = os.path.join(MEDIA_ROOT, out_path)
    with open(path, "w") as text_file:
        text_file.write(text)

    print("text punctuated successfully!")

    return out_path
