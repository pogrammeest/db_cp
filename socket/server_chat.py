import socket
from typing import Literal
import bcrypt
import prettytable

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
        self.authorized_users = {}
        self.admins = {}
        self.registered_commands = {
            "/chat": {"root": "server", "request": "chat"},
            "/clear": {"root": "server", "request": "clear"},
        }

    def set_up(self):
        self.socket.bind((self.address, self.port))
        self.socket.listen()
        self.socket.setblocking(False)
        logger.info("Server listing...")

    async def send_data_to_everyone(self, **kwargs):
        for user in self.users:
            try:
                await super(Server, self).send_data(where=user, data=kwargs["data"])
            except SocketException as exc:
                logger.info(exc)
                user.close()

    def is_admin(self, user_socket):
        if self.admins.get(user_socket):
            return True
        return False

    def get_role(self, user_socket) -> Literal["unauthorized", "authorized", "admin"]:
        if self.admins.get(user_socket):
            return "admin"
        if self.authorized_users.get(user_socket):
            return "authorized"
        return "unauthorized"

    def get_authorized_users(self):
        return list(self.authorized_users.keys()) + list(self.admins.keys())

    def get_help_message(self, role: Literal["unauthorized", "authorized", "admin"]):
        base_commands = [
            "/help - описание",
            "/login - авторизоваться",
            "/db - увидеть список доступных таблиц",
            "/chat - включить/выключить режим чата",
            "/clear - очистить экран",
            "/reg - регистрация",
        ]
        authorized_commands = [
            "/my_projects - мои проекты",
            "/my_tasks - мои задачи",
        ]
        admin_commands = [
            "/db_del - удаление таблиц",
            "/db_update - обновление таблиц",
            "/shut_down - выключение сервера (требуется подтверждение)",
            "/disconnection_server [пароль] - подтверждение выключения",
        ]

        commands = base_commands
        if role == "admin":
            commands += authorized_commands + admin_commands
        if role == "authorized":
            commands += authorized_commands
        return {
            "root": "server",
            "message_text": "Список доступных команд:\n" + "\n".join(commands),
        }

    def reg(self, data):
        try:
            username, email, password = (
                data["message_text"].split()[1],
                data["message_text"].split()[2],
                data["message_text"].split()[3],
            )

            user_exists = self.db.select_one_row(
                table="users", condition=f"username = '{username}' OR email = '{email}'"
            )
            if user_exists:
                return {
                    "root": "server",
                    "message_text": "Пользователь с таким именем или email уже существует.",
                }

            # Хешируем пароль
            hashed_password = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            self.db.insert(
                table="users",
                columns="username, email, password_hash, role_id",
                values=(username, email, hashed_password, 3),
            )
            return {
                "root": "server",
                "message_text": "Регистрация успешна! Введите /login [username] [password] для входа.",
            }
        except IndexError:
            return {
                "root": "server",
                "message_text": "Формат: /reg [username] [email] [password]",
            }
        except Exception as exc:
            logger.info(exc)
            return {
                "root": "server",
                "message_text": f"Ошибка при регистрации: {exc}",
            }

    def login(self, data, listened_socket):
        try:
            username, password = (
                data["message_text"].split()[1],
                data["message_text"].split()[2],
            )

            user = self.db.select_one_row(
                table="users",
                columns="id, username, password_hash",
                condition=f"username = '{username}'",
            )

            if not user:
                return {
                    "root": "server",
                    "message_text": "Неверный логин или пароль.",
                }

            user_id, _, stored_hash = user

            if not bcrypt.checkpw(
                password.encode("utf-8"), stored_hash.encode("utf-8")
            ):
                return {
                    "root": "server",
                    "message_text": "Неверный логин или пароль.",
                }

            for sock in self.get_authorized_users():
                if sock["socket"] == listened_socket:
                    raise SocketException

            # Проверяем роль
            is_admin = self.db.select_one_row(
                table="users u JOIN roles r ON u.role_id = r.id",
                columns="r.name",
                condition=f"u.id = {user_id} AND r.name = 'admin'",
            )

            if is_admin:
                self.admins[listened_socket] = user_id
                self.registered_commands["/help"][
                    "message_text"
                ] += "\n  /db_del - удаление таблиц\n  /db_update - обновление таблиц"
            else:
                self.authorized_users[listened_socket] = user_id

            return {
                "root": "server",
                "message_text": f"Добро пожаловать, {username}!",
            }
        except IndexError:
            return {
                "root": "server",
                "message_text": "Формат: /login [username] [password]",
            }
        except SocketException:
            return {
                "root": "server",
                "message_text": "Вы уже авторизованы!",
            }
        except Exception as exc:
            logger.info(exc)
            return {
                "root": "server",
                "message_text": f"Ошибка при авторизации: {exc}",
            }

    def my_projects(self, user_id: int):
        try:
            projects = self.db.get_my_projects(user_id)
            if projects:
                table = prettytable.PrettyTable()
                table.field_names = ["ID", "Название", "Описание", "Создано"]
                for row in projects:
                    table.add_row(row)
                msg = "Твои проекты: \n" + str(table)
            else:
                msg = "У вас пока нет проектов."
        except Exception as e:
            logger.error(f"[my_projects] Ошибка: {e}")
            msg = "Ошибка при получении проектов."
        return {
            "root": "server",
            "message_text": msg,
            "request": "show_db",
        }

    def my_tasks(self, user_id: int):
        try:
            tasks = self.db.get_my_tasks(user_id)
            if tasks:
                table = prettytable.PrettyTable()
                table.field_names = [
                    "ID",
                    "Название",
                    "Описание",
                    "Статус",
                    "Создано",
                    "Срок",
                    "Проект",
                    "Автор",
                ]
                for row in tasks:
                    table.add_row(row)
                msg = "Твои задачи: \n" + str(table)
            else:
                msg = "У вас нет назначенных задач."
        except Exception as e:
            logger.error(f"[my_tasks] Ошибка: {e}")
            msg = "Ошибка при получении задач."
        return {
            "root": "server",
            "message_text": msg,
            "request": "show_db",
        }

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

    def assign_task(self, task_id: int, user_id: int):
        try:
            success = self.db.assign_task(task_id, user_id)
            return (
                "Пользователь назначен на задачу."
                if success
                else "Ошибка: задача не найдена или пользователь уже назначен."
            )
        except Exception as e:
            logger.error(f"[assign_task] Ошибка: {e}")
            return "Ошибка при назначении задачи."

    def add_task_comment(self, task_id: int, user_id: int, message: str):
        try:
            self.db.add_task_comment(task_id, user_id, message)
            return "Комментарий добавлен."
        except Exception as e:
            logger.error(f"[add_task_comment] Ошибка: {e}")
            return "Ошибка при добавлении комментария."

    def get_task_comments(self, task_id: int):
        try:
            comments = self.db.get_task_comments(task_id)
            if not comments:
                return "Комментариев нет."

            table = prettytable.PrettyTable()
            table.field_names = ["ID", "Пользователь", "Комментарий", "Дата"]
            for row in comments:
                table.add_row(row)
            return str(table)
        except Exception as e:
            logger.error(f"[get_task_comments] Ошибка: {e}")
            return "Ошибка при получении комментариев."

    def create_project(self, name: str, description: str, created_by: int):
        try:
            self.db.create_project(name, description, created_by)
            return "Проект успешно создан."
        except Exception as e:
            logger.error(f"[create_project] Ошибка: {e}")
            return "Ошибка при создании проекта."

    def verify_request(self, data: dict, listened_socket: socket.socket):
        sending_data = {}
        if data["message_text"] == "/help":
            sending_data = self.get_help_message(self.get_role(listened_socket))
        elif "/db_del" in data["message_text"] and self.is_admin(listened_socket):
            sending_data = self.db_del(data)
        elif "/db_update" in data["message_text"] and self.is_admin(listened_socket):
            sending_data = self.db_update(data)
        elif "/my_projects" in data["message_text"] and self.authorized_users.get(
            listened_socket, False
        ):
            sending_data = self.my_projects(self.authorized_users[listened_socket])
        elif "/my_tasks" in data["message_text"] and self.authorized_users.get(
            listened_socket, False
        ):
            sending_data = self.my_tasks(self.authorized_users[listened_socket])
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
                "message_text": "Похоже такой команды нет или вы не авторизованны, пожалуйста введите /help для получение списка доступных команд",
            }
        return sending_data

    async def listen_socket(self, listened_socket: socket.socket):
        while True:
            try:
                data = await super(Server, self).listen_socket(listened_socket)
                data = data["data"]
                if data["chat_is_working"] and data["message_text"] != "/chat":
                    await self.send_data_to_everyone(data=data)
                elif "/start" in data["message_text"]:

                    await self.send_data(
                        where=listened_socket,
                        data={
                            "root": "server",
                            "message_text": "Привет, пишет сервер, если хочешь увидеть список доступных команд напиши /help",
                            "message_time": f"{datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}",
                        },
                    )
                elif "/exit" in data["message_text"]:
                    await self.send_data(
                        where=listened_socket,
                        data={
                            "root": "server",
                            "command": "disconnect",
                        },
                    )

                    self.authorized_users.pop(listened_socket, None)
                    self.admins.pop(listened_socket, None)
                    self.users.remove(listened_socket)
                    logger.info(
                        f"User {listened_socket.getsockname()[0]} disconnected!"
                    )
                    listened_socket.close()
                    return
                elif "/shut_down" in data["message_text"]:
                    if self.is_admin(listened_socket):
                        self.confirm_shut_down = True
                        await self.send_data(
                            where=listened_socket,
                            data={
                                "root": "server",
                                "message_text": "Для подтверждения введите: /disconnection_server [спец пароль]",
                            },
                        )
                    else:
                        await self.send_data(
                            where=listened_socket,
                            data={
                                "root": "server",
                                "message_text": "У вас недостаточно прав!",
                            },
                        )
                elif "/disconnection_server" in data["message_text"]:
                    if not self.is_admin(listened_socket):
                        await self.send_data(
                            where=listened_socket,
                            data={
                                "root": "server",
                                "message_text": "У вас недостаточно прав!",
                            },
                        )
                    elif not self.confirm_shut_down:
                        await self.send_data(
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
                                await self.send_data(
                                    where=listened_socket,
                                    data={
                                        "root": "server",
                                        "message_text": "Здесь должно было быть выключение, но у меня плохо с пониманием event_loop по-этому пока его здесь нет",
                                    },
                                )
                            else:
                                self.confirm_shut_down = False
                                await self.send_data(
                                    where=listened_socket,
                                    data={
                                        "root": "server",
                                        "message_text": "Пароль не верен! Подтверждение сброшено!",
                                    },
                                )
                        except Exception as exc:
                            logger.info(exc)
                            await self.send_data(
                                where=listened_socket,
                                data={
                                    "root": "server",
                                    "message_text": "Для подтверждения введите: /disconnection_server [спец пароль]",
                                },
                            )
                else:
                    sending_data = self.verify_request(data, listened_socket)
                    await self.send_data(where=listened_socket, data=sending_data)
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

    async def main(self):
        await self.main_loop.create_task(self.accept_socket())


if __name__ == "__main__":
    server = Server()
    server.set_up()
    server.start()
