"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport


    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None


    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                check_login = decoded.replace("login:", "").replace("\r\n", "")
                for _ in self.server.clients:
                    if check_login == _.login:
                        self.transport.write(
                            f"Логин {check_login} занят, попробуйте другой.".encode()

                        )
                        self.transport.close()

                self.login = check_login

                if len(self.server.history) == 0:
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                else:
                    self.transport.write(
                        f"Привет, {self.login}!\n{self.send_history()}\n".encode()
                    )

        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.history.append(format_string)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        ind = 10 if len(self.server.history) > 10 else len(self.server.history)
        for mess in self.server.history[-ind:]:
            self.transport.write(f'{mess}\n'.encode())


    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list


    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
