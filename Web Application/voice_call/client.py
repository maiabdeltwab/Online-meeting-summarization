""" client side for call server """

import socket
import threading
import pyaudio
from app.models import group_members

# pylint: disable=bare-except

class Client:
    """ client for group call """

    def __init__(self, ip, port, group_member):
        self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.group_member = group_member
        while 1:
            try:
                self.target_ip = ip
                self.target_port = port
                self.sckt.connect((self.target_ip, self.target_port))
                break
            except:
                print("Couldn't connect to server")
                break

        chunk_size = 1024  # 512
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 20000

        # initialise microphone recording
        self.audio = pyaudio.PyAudio()
        self.playing_stream = self.audio.open(format=audio_format, channels=channels,
                                              rate=rate, output=True, frames_per_buffer=chunk_size)
        self.recording_stream = self.audio.open(format=audio_format, channels=channels,
                                                rate=rate, input=True, frames_per_buffer=chunk_size)

        print("Connected to Server")

        # start threads
        threading.Thread(target=self.receive_server_data).start()
        threading.Thread(target=self.send_data_to_server).start()

    def receive_server_data(self):
        """ client server data from server """
        while True:
            try:
                self.group_member = group_members.objects.filter(
                    pk=self.group_member.id).first()
                data = self.sckt.recv(1024)
                self.playing_stream.write(data)
                if self.group_member.in_call == 0:
                    print('disconnect client')
                    break
            except:
                pass

    def send_data_to_server(self):
        """ send data form client to server """
        while True:
            try:
                self.group_member = group_members.objects.filter(
                    pk=self.group_member.id).first()
                data = self.recording_stream.read(1024)
                self.sckt.sendall(data)
                if self.group_member.in_call == 0:
                    print('client stop send')
                    break
            except:
                pass


#Client('192.168.1.5',8080)
