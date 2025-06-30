from OOP_Socket import Socket
import asyncio
from datetime import datetime
from os import system
from Encryption import Encryptor
from Exceptions import SocketException
from sys import platform
import json
import sys
import time
from threading import Thread


class Client(Socket):
    def __init__(self):
        self.chat_is_working = False
        self.messages = ""
        self.encryptor = Encryptor()

        super(Client, self).__init__()

    def set_up(self):
        try:
            self.socket.connect((self.address, self.port))

        except ConnectionError:
            for i in range(7, -1, -1):
                if platform == "win32":
                    system("cls")
                else:
                    system("clear")
                print("Sorry, server is offline")
                print("This program will close in %d seconds" % i)
                time.sleep(1)
            if platform == "win32":
                system("cls")
            else:
                system("clear")
            print("Good bye...")
            time.sleep(1)
            exit(0)
        self.socket.setblocking(False)

    def registration(self):
        sending_data = {
            "name": "",
            "email": "",
            "password": "",
        }
        valid_pass = False

        input()

        print("Начнем регистрацию!\nИмя:")

        sending_data["name"] = input()
        print("\nПочтa:")
        sending_data["email"] = input()
        while not valid_pass:
            print("\nПароль:")
            sending_data["password"] = input()
            print("\nповторите пароль:")
            repeat_pass = input()
            if sending_data["password"] == repeat_pass:
                valid_pass = True
            else:
                print("Пароли не совподают пожалуйста, повторите попытку!")
        print("Вы успешно зарегестриравнны!\n")
        print("\n")
        print(sending_data)
        input()
        return sending_data

    async def listen_socket(self, listened_socket):
        while True:
            try:
                if not self.is_working:
                    return
                try:
                    data = await super(Client, self).listen_socket(listened_socket)
                except SocketException as exc:
                    print(exc)
                    self.is_working = False
                    break
                data = data["data"]
                if data["root"] == "server" and "request" in data:
                    if data["request"] == "chat":
                        if not self.chat_is_working:
                            self.chat_is_working = True
                            self.messages += f"$$SERVER MESSAGE$$: чат включен\n"
                        else:
                            self.chat_is_working = False
                            self.messages += f"$$SERVER MESSAGE$$: чат выключен\n"
                    elif data["request"] == "clear":
                        self.messages = "Экран очищен\n"
                    elif data["request"] == "show_db":
                        self.messages += data["message_text"] + "\n"
                    elif data["request"] == "reg":
                        self.messages = "Экран очищен\n"
                elif data["root"] == "server":
                    self.messages += f"$$SERVER MESSAGE$$:{data['message_text']}\n"
                elif data["root"] == "user" and self.chat_is_working:
                    self.messages += f"{data['message_time']}:{data['message_text']}\n"

                if platform == "win32":
                    system("cls")
                else:
                    system("clear")
                print(self.messages)
            except (SocketException, ConnectionError):
                print("\n Server is offline...")
                time.sleep(5)
                exit(0)

    async def send_data(self, data=None):
        while True:
            message = await self.main_loop.run_in_executor(None, input, "")
            if not self.is_working:
                return

            encrypted_data = {
                "root": "user",
                "chat_is_working": self.chat_is_working,
                "message_text": message,
                "message_time": f"{datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}",
            }
            if not self.chat_is_working:
                self.messages += "$$>" + message + "\n"
            await super(Client, self).send_data(where=self.socket, data=encrypted_data)

    async def main(self):
        await asyncio.gather(
            self.main_loop.create_task(self.listen_socket(self.socket)),
            self.main_loop.create_task(self.send_data()),
        )


if __name__ == "__main__":
    client = Client()
    client.set_up()
    client.start()
