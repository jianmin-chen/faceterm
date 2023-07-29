from colorama import just_fix_windows_console, Fore, Style
from config import timeout
import argparse, json, socket, threading


def send(host: str, port: int, data: dict):
    """
    Send message to port on host.

        Parameters:
            host (str)
            port (int)
            data (dict)

        Returns:
            status (dict): Returns response from server, if any.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.settimeout(timeout)
    s.send(json.dumps(data).encode())
    fragments = []
    while True:
        chunk = s.recv(1024)
        fragments.append(chunk)
        if len(chunk) < 1024:
            break
    status = json.loads((b"".join(fragments)).decode("ascii"))
    return status, s


class Client:
    @classmethod
    def authenticate(cls, host: str, port: int, username: str, password: str):
        status, s = send(
            host, port, {"route": "signup", "username": username, "password": password}
        )

    @classmethod
    def signup(cls, host: str, port: int, username: str, password: str):
        status, s = send(
            host, port, {"route": "signup", "username": username, "password": password}
        )
        s.shutdown(socket.SHUT_RDWR)
        return status["uuid"]

    def __init__(self, username: str, password: str, host: str, port: int):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.conn = None

    def listen(self):
        """
        Continously listen for messages from the server in case of new messages.
        """

        if self.conn is not None:
            fragments = []
            while True:
                chunk = self.conn.recv(1024)
                if chunk:
                    fragments.append(chunk.decode("ascii"))
                    if fragments[-1].endswith("}"):
                        pass

    def create(self, name: str):
        status, s = send(
            self.host,
            self.port,
            {
                "route": "create",
                "username": self.username,
                "password": self.password,
            },
        )


if __name__ == "__main__":
    just_fix_windows_console()

    host = "10.10.1.47"
    port = 5000

    parser = argparse.ArgumentParser(
        prog="FaceTerm",
        description="FaceTime in the terminal",
    )

    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("-c", "--color", action="store_true")
    parser.add_argument("-j", "--join")
    parser.add_argument("-h", "--host")
    parser.add_argument("-p", "--port")

    args = parser.parse_args()

    username = args.username
    password = args.password
    color = args.color
    code = args.join
    host = args.host or ""
    port = args.port or 5000

    authenticate = Client.authenticate(host, port, username, password)
    if authenticate["status"] is None:
        # Sign user for an account
        uuid = Client.signup(host, port, username, password)
        print(f"{Style.BRIGHT}Signed up for an account{Style.RESET_ALL}")
    elif not authenticate["status"]:
        print(f"{Style.BRIGHT}Invalid password. Try again?{Style.RESET_ALL}")
        exit(0)
    else:
        uuid = authenticate

    client = Client(username, password, host, port)
    if code is None:
        # Start a meeting!
        pass
    else:
        pass

    while True:
        try:
            pass
        except KeyboardInterrupt:
            client.signout()
            exit(0)
        except Exception as e:
            client.signout()
            print("Whoops, something caused the client to crash:", e)
            exit(-1)
