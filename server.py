#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def send_history(self, message):
        if len(self.server.list_history) < 10:
            self.server.list_history.append(message)
        else:
            del self.server.list_history[0]
            self.server.list_history.append(message)
        return self.server.list_history

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "").replace(" ", "")
                if self.login not in self.server.con_user:
                    self.server.con_user.append(self.login)
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.transport.write(f"Пользователи которые сейчас в сети {self.server.con_user}\n".encode())
                    for mass in self.server.list_history:
                        self.transport.write(f"{mass}\n".encode())
                elif self.login in self.server.con_user:
                    self.transport.write(f"Логин '{self.login}' занят!\n".encode())
                    del self.login
                    self.transport.close()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        self.transport.write("""Для авторизации введите login: name{}\n""".format("=" * 35).encode())
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")
        self.server.con_user.remove(self.login)

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.send_history(message.replace("\r\n\n", ""))

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    con_user: list
    list_history: list

    def __init__(self):
        self.clients = []
        self.con_user = []
        self.list_history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
