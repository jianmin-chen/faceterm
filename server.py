import json, socket

class Server:
    def __init__(self, ip_address: str, port: int, max_connections: int=10, bufsize: int=1024):
        self.ip_address = ip_address
        self.port = port
        self.max_connections = max_connections
        self.bufsize = bufsize
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip_address, self.port))
        self.socket.setblocking(False)
        self.socket.listen(max_connections)

    def close(self):
        """
        Close socket.
        """

        self.socket.shutdown(socket.SHUT_RDWR)

    def receive(self):
        connection = None
        try:
            connection, address = self.socket.accept()
            fragments = []
            while True:
                chunk = connection.recv(self.bufsize)
                fragments.append(chunk)
                if len(chunk) < self.bufsize:
                    break