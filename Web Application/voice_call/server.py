""" call server """

import socket
import threading
from contextlib import closing
from app.models import Group

# pylint: disable=bare-except

class Server:
    """ call server """

    def find_free_port(self):
        """ use this function to obtain free available port """
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sckt:
            sckt.bind(('', 0))
            sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return sckt.getsockname()[1]

    def __init__(self, ip, group):
        self.server_ip = ip
        self.group = group
        while 1:
            try:
                self.port = self.find_free_port()
                print(self.port)
                self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sckt.bind((self.server_ip, self.port))
                break
            except:
                print("Couldn't bind to that port")
                break

        self.connections = []
        threading.Thread(target=self.accept_connections).start()

    def accept_connections(self):
        """  accept connections function """
        self.sckt.listen(100)

        print('Running on IP: '+self.server_ip)
        print('Running on port: '+str(self.port))

        while True:
            try:
                c, addr = self.sckt.accept()
                self.connections.append(c)
                threading.Thread(target=self.handle_client,
                                 args=(c, addr)).start()

                self.group = Group.objects.filter(pk=self.group.id).first()
                if self.group.call_state == 0:
                    print('server accept connections')
                    self.sckt.close()
                    break

            except:
                pass

    def broadcast(self, sock, data):
        """ this method send data broadcasting to clients """
        for client in self.connections:
            if client not in (self.sckt, sock):
                try:
                    client.send(data)
                except:
                    pass

    # pylint: disable=unused-argument
    def handle_client(self, c, addr):
        """ handel client side """
        while 1:
            try:
                data = c.recv(1024)
                self.broadcast(c, data)

                self.group = Group.objects.filter(pk=self.group.id).first()
                if self.group.call_state == 0:
                    print('server stop handle client')
                    c.close()
                    self.sckt.close()
                    break
            except socket.error:
                c.close()
