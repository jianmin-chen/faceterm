from config import timeout
from db import Database
import socket, hashlib, json, threading


empty = lambda d, keys: False in [d.get(key) is not None for key in keys]


class Meeting:
    def __init__(self, initial_client: socket.socket):
        self.host = initial_client
        self.connections = [self.host]
        self.code = hashlib.sha1(initial_client.getpeername()).hexdigest()

    def forward_image(self, data, color):
        for client in self.connections:
            pass


class Server:
    def __init__(self, host: str, port: int, backlog: int = 10, bufsize: int = 1024):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.bufsize = bufsize
        self.meetings = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.routes = {}

    def close(self):
        """
        Close socket.
        """

        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass

    def listen(self):
        self.socket.listen(self.backlog)
        while True:
            client, address = self.socket.accept()
            client.settimeout(timeout)
            thread = threading.Thread(target=self.receive, args=(client, address))
            thread.daemon = True
            thread.start()

    def receive(self, client, address):
        try:
            fragments = []
            while True:
                chunk = client.recv(self.bufsize)
                fragments.append(chunk)
                if len(chunk) < self.bufsize:
                    break
            self.respond(
                client, address, json.loads((b"".join(fragments)).decode("utf-8"))
            )
        except:
            print("Whoops, an error occurred:", e)
            self.send(client, {"code": 500, "reason": str(e)})

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop("endpoint", None)
            self.routes[endpoint] = rule
            return f

        return decorator

    def respond(self, client, address, data):
        try:
            if empty(data, ["route"]):
                # Route not provided
                raise Exception()
            response = self.routes[data["route"]]
            self.send(client, response)
        except Exception:
            return self.send(client, {"code": 404, "reason": "Not Found"})

    def send(self, client, data: dict):
        client.send(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def available_port(start: int, max_search: int = 10):
    """
    Test for available ports, starting from given argument.

    Parameters:
        start (int)

    Returns:
        available (int)
    """

    available = start
    query = 0
    while query < max_search:
        # Search for available ports
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("0.0.0.0", available))
            s.close()
            return available
        except:
            s.close()
            available += 1
            query += 1
    raise Exception(f"Unable to find available port from range {start} to {available}.")


if __name__ == "__main__":
    port = available_port(5000)
    print("Listening on port:", port)

    server = Server("0.0.0.0", port)

    @server.route("/auth")
    def auth(data, sref: Server):
        if empty(data, ["username", "passowrd"]):
            return {"code": 401, "reason": "Username and/or password not provided"}
        status = sref.db.authenticate(data["username"], data["password"])
        return {"code": 200, "status": status}

    @server.route("/signup")
    def signup(data, sref: Server):
        if empty(data, ["username", "password"]):
            return {"code": 401, "reason": "Username and/or password not provided"}
        uuid = sref.db.signup(data["username"], data["password"])
        return {"code": 200, "uuid": uuid}

    @server.route("/join")
    def join(data, sref: Server):
        if empty(data, ["username", "password", "code"]):
            return {
                "code": 401,
                "reason": "Username, password, and/or code not provided",
            }
        status = sref.db.authenticate(data["username"], data["password"])
        if not status:
            return {"code": 401, "reason": "Invalid authentication"}

    @server.route("/signout")
    def signout(data, sref: Server):
        if empty(data, ["username", "password", "code"]):
            return {
                "code": 401,
                "reason": "Username, password, and/or code not provided",
            }
        status = sref.db.authenticate(data["username"], data["password"])
        if not status:
            return {"code": 401, "reason": "Invalid authentication"}

    try:
        server.listen()
    except KeyboardInterrupt:
        server.close()
        print("KeyboardInterrupt, shutting down")
    except Exception as e:
        server.close()
        print("Whoops, something caused the server to crash:", e)
