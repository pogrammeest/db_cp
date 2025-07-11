from oop_socket import Socket
from utils import logger
from exception import SocketException
from datetime import datetime
from working_with_db import WorkingWithDataBase


class Server(Socket):

    def __init__(self):
        super(Server, self).__init__()
        self.db = WorkingWithDataBase()
        self.confirm_shut_down = False
        self.users = []
        self.authorized_users = []
        self.admins = []
        self.registered_commands = {
            "/help": {
                "root": "server",
                "message_text": """Список текущих доступных команд:\n/help - описание\n/login - авторизоваться\n/db - увидеть список доступных таблиц\n/chat - включить/выключить режим чата\n/clear - очистить экран\n/reg - регистрация""",
            },
            "/chat": {"root": "server", "request": "chat"},
            "/clear": {"root": "server", "request": "clear"},
        }

    def set_up(self):
        self.socket.bind((self.address, self.port))
        self.socket.listen()
        self.socket.setblocking(False)
        logger.info("Server listing...")

    async def send_data(self, **kwargs):
        for user in self.users:
            try:
                await super(Server, self).send_data(where=user, data=kwargs["data"])
            except SocketException as exc:
                logger.info(exc)
                user.close()

    def is_admin(self, user_socket):
        for admin in self.admins:
            if user_socket == admin["socket"]:
                return True
        return False

    def reg(self, data):
        try:
            login, email, password = (
                data["message_text"].split()[1],
                data["message_text"].split()[2],
                data["message_text"].split()[3],
            )
            self.db.insert(
                table="gamers",
                columns="name, email, password",
                values=(login, email, password),
            )
            return {
                "root": "server",
                "message_text": "Регистрация прошла успешно, теперь входите!",
            }
        except IndexError:
            return {
                "root": "server",
                "message_text": "Пожалуйста, введите /reg [login] [email] [password]",
            }
        except Exception as exc:
            logger.info(exc)

    def db_del(self, data):
        try:
            table, condition = (
                data["message_text"].split()[1],
                data["message_text"].split()[2],
            )
            self.db.delete(table, condition)
        except IndexError:
            return {
                "root": "server",
                "message_text": " Пожалуйста, введите /db_del [таблица] [условие]",
            }
        except BaseException as err:
            self.db.conn.rollback()
            return {
                "root": "server",
                "message_text": f" Пожалуйста, проверьте запрос! Ошибка:\n{err}",
            }

        else:
            return {
                "root": "server",
                "message_text": f" Запрос на удаление в таблице '{table}' успешно выполнен\n",
            }

    def db_update(self, data):
        try:
            table, set_string, condition = (
                data["message_text"].split()[1],
                data["message_text"].split()[2],
                data["message_text"].split()[3],
            )
            self.db.update(table, set_string, condition)
        except IndexError:
            return {
                "root": "server",
                "message_text": " Пожалуйста, введите /db_update [table] ['set_string'] [условие]",
            }
        except BaseException as err:
            self.db.conn.rollback()
            return {
                "root": "server",
                "message_text": f" Пожалуйста, проверьте запрос! Ошибка:\n{err}",
            }
        else:
            return {
                "root": "server",
                "message_text": f" Запрос на обновление в таблице '{table}' успешно выполнен!\n",
            }

    def find_table(self, data):
        if not (len(data["message_text"].split()) < 2):
            try:
                table = data["message_text"].split()[1]
                sending_data = self.db.select_all_rows(table=table)[0]
                return {
                    "root": "server",
                    "message_text": sending_data.get_string(),
                    "request": "show_db",
                }
            except:
                return {
                    "root": "server",
                    "message_text": "Таблица не найдена, полный список таблиц: \n"
                    + "\n".join(self.db.get_table_name()),
                    "request": "show_db",
                }
        else:
            return {
                "root": "server",
                "message_text": "Полный список таблиц: \n"
                + "\n".join(self.db.get_table_name()),
                "request": "show_db",
            }

    def login(self, data, listened_socket):
        try:
            login, password = (
                data["message_text"].split()[1],
                data["message_text"].split()[2],
            )
            user = self.db.select_one_row(
                table="gamers",
                condition=f"name = '{login}' and password = '{password}'",
            )
            for sock in self.authorized_users + self.admins:
                if listened_socket == sock["socket"]:
                    raise SocketException
            if user is None:
                return {
                    "root": "server",
                    "message_text": "Пользователь не найден!",
                }
            else:
                if user[-1]:
                    self.admins.append({"id": user[0], "socket": listened_socket})
                    self.registered_commands["/help"][
                        "message_text"
                    ] += "\n  /db_del - удаление таблиц \n  /db_update - обновление таблиц"
                else:
                    self.authorized_users.append(
                        {"id": user[0], "socket": listened_socket}
                    )
                return {"root": "server", "message_text": "Вы вошли!"}
        except IndexError:
            return {
                "root": "server",
                "message_text": "Пожалуйста, введите /login [логин] [пароль]",
            }
        except SocketException:
            return {
                "root": "server",
                "message_text": "Вы уже авторизовались!",
            }
        finally:
            logger.info(self.admins)

    def verify_request(self, data: dict, listened_socket: Socket):
        sending_data = {}
        if data["message_text"] in self.registered_commands:
            sending_data = self.registered_commands[data["message_text"]]
        elif "/db_del" in data["message_text"] and self.is_admin(listened_socket):
            sending_data = self.db_del(data)
        elif "/db_update" in data["message_text"] and self.is_admin(listened_socket):
            sending_data = self.db_update(data)
        elif "/db" in data["message_text"]:
            sending_data = {
                "root": "server",
                "message_text": "У вас недостаточно прав! Пожалуйста авторизуйтесь под администратором!",
            }
            if self.is_admin(listened_socket):
                sending_data = self.find_table(data)
        elif "/login" in data["message_text"]:
            sending_data = self.login(data, listened_socket)
        elif "/reg" in data["message_text"]:
            sending_data = self.reg(data)
        else:
            sending_data = {
                "root": "server",
                "message_text": "Похоже такой команды нет, пожалуйста введите /help для получение списка",
            }

        return sending_data

    async def listen_socket(self, listened_socket=None):
        while True:
            try:
                data = await super(Server, self).listen_socket(listened_socket)
                data = data["data"]
                if data["chat_is_working"] and data["message_text"] != "/chat":
                    await self.send_data(data=data)
                elif "/exit" in data["message_text"]:
                    await super(Server, self).send_data(
                        where=listened_socket,
                        data={
                            "root": "server",
                            "command": "disconnect",
                        },
                    )
                    self.users.remove(listened_socket)
                    listened_socket.close()
                    return
                elif "/shut_down" in data["message_text"]:
                    if self.is_admin(listened_socket):
                        self.confirm_shut_down = True
                        await super(Server, self).send_data(
                            where=listened_socket,
                            data={
                                "root": "server",
                                "message_text": "Для подтверждения введите: /disconnection_server [спец пароль]",
                            },
                        )
                    else:
                        await super(Server, self).send_data(
                            where=listened_socket,
                            data={
                                "root": "server",
                                "message_text": "У вас недостаточно прав!",
                            },
                        )
                elif "/disconnection_server" in data["message_text"]:
                    if not self.is_admin(listened_socket):
                        await super(Server, self).send_data(
                            where=listened_socket,
                            data={
                                "root": "server",
                                "message_text": "У вас недостаточно прав!",
                            },
                        )
                    elif not self.confirm_shut_down:
                        await super(Server, self).send_data(
                            where=listened_socket,
                            data={
                                "root": "server",
                                "message_text": "Не было подтверждения от предыдущей команды!",
                            },
                        )
                    else:
                        try:
                            if data["message_text"].split()[1] == "4321":
                                # TODO: переписать блокирующие функции так, чтобы можно было выключить сервер и клиенты это обработали
                                await super(Server, self).send_data(
                                    where=listened_socket,
                                    data={
                                        "root": "server",
                                        "message_text": "Здесь должно было быть выключение, но у меня плохо с пониманием event_loop по-этому пока его здесь нет",
                                    },
                                )
                            else:
                                self.confirm_shut_down = False
                                await super(Server, self).send_data(
                                    where=listened_socket,
                                    data={
                                        "root": "server",
                                        "message_text": "Пароль не верен! Подтверждение сброшено!",
                                    },
                                )
                        except Exception as exc:
                            logger.info(exc)
                            await super(Server, self).send_data(
                                where=listened_socket,
                                data={
                                    "root": "server",
                                    "message_text": "Для подтверждения введите: /disconnection_server [спец пароль]",
                                },
                            )
                else:
                    sending_data = self.verify_request(
                        data, listened_socket=listened_socket
                    )
                    await super(Server, self).send_data(
                        where=listened_socket, data=sending_data
                    )
            except SocketException as exc:
                logger.info(
                    f"User {listened_socket.getsockname()[0]} has disconnected."
                )
                self.users.remove(listened_socket)
                listened_socket.close()
                return

    async def accept_socket(self):
        while True:
            client_socket, client_address = await self.main_loop.sock_accept(
                self.socket
            )
            logger.info(f"User {client_address[0]} connected!")
            self.users.append(client_socket)
            self.main_loop.create_task(self.listen_socket(client_socket))
            await super(Server, self).send_data(
                where=client_socket,
                data={
                    "root": "server",
                    "message_text": "Привет, пишет сервер, если хочешь увидеть список доступных команд напиши /help",
                    "message_time": f"{datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}",
                },
            )

    async def main(self):
        await self.main_loop.create_task(self.accept_socket())


if __name__ == "__main__":
    server = Server()
    server.set_up()
    server.start()
