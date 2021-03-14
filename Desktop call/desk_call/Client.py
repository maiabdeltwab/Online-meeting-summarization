import socket
import sys
import threading

import pyaudio

import cx_Oracle

class Client:

    in_call = 1    

    def __init__(self, ip, port, group_member):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.group_member = group_member
        while 1:
            try:
                self.target_ip = ip 
                self.target_port =  port 
                self.s.connect((self.target_ip, self.target_port))
                break
            except:
                print("Couldn't connect to server")
                break

        chunk_size = 1024 # 512
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 20000

        # initialise microphone recording
        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk_size)
        self.recording_stream = self.p.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size)
        
        print("Connected to Server")

        # start threads
        threading.Thread(target=self.receive_server_data).start()
        threading.Thread(target=self.send_data_to_server).start()       

    
    def receive_server_data(self):
        while True:
            try:
                data = self.s.recv(1024)
                self.playing_stream.write(data)
                if self.in_call == 0:
                    print('disconnect client')
                    break
            except:
                pass


    def send_data_to_server(self):
        while True:
            try:

                data = self.recording_stream.read(1024)
                self.s.sendall(data)

                if self.in_call == 0:
                    print('client stop send')
                    break
            except:
                pass

    def end_call(self):
       self.in_call = 0


#Client('192.168.1.5',8080)
