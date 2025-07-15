import os
from typing import Any
import psycopg2
import prettytable
from utils import logger
from dotenv import load_dotenv


class WorkingWithDataBase:
    def __init__(self):
        load_dotenv()
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
        )
        self.cursor = self.conn.cursor()

    def select_many_rows(self, table, columns="*", condition=""):
        select_many_rows_command = f"select {columns} from {table} where {condition}"
        self.cursor.execute(select_many_rows_command)

        return self.cursor.fetchall()

    def select_one_row(self, table, columns="*", condition=""):
        select_one_row_command = f"select {columns} from {table} where {condition}"
        self.cursor.execute(select_one_row_command)

        return self.cursor.fetchone()

    def select_all_rows(
        self, columns="*", table="table"
    ) -> tuple[Any, list[tuple[Any, ...]]]:
        try:
            select_many_rows_command = f"select {columns} from {table} "
            self.cursor.execute(select_many_rows_command)
            tuple_data = self.cursor.description
            name_columns = []
            for i in tuple_data:
                name_columns.append(i[0])
            temp_data = self.cursor.fetchall()

            lovely = prettytable.PrettyTable()
            lovely.field_names = name_columns
            for i in temp_data:
                lovely.add_row(i)
            return (lovely, temp_data)
        except Exception as exc:
            self.conn.rollback()
            raise exc

    def get_table_name(self):
        get_table_name_command = f"SELECT table_name FROM information_schema.tables  where table_schema='public' ORDER BY table_name;"
        self.cursor.execute(get_table_name_command)
        data = []
        for table in self.cursor.fetchall():
            data.append(table[0])
        return data

    def update(
        self, table, set_string="", condition=""
    ):  # UPDATE weather SET temp_lo = temp_lo+1, temp_hi = temp_lo+15, prcp = DEFAULT WHERE city = 'San Francisco' AND date = '2003-07-03'

        update_command = f"UPDATE {table} SET {set_string} WHERE {condition}"
        self.cursor.execute(update_command)
        self.conn.commit()

    def delete(self, table, condition=""):  # DELETE FROM films WHERE kind <> 'Musical';

        delete_command = f"DELETE FROM {table} WHERE {condition}"
        self.cursor.execute(delete_command)
        self.conn.commit()

    def insert(self, table="", columns="", values=()):
        insert_command_string = (
            f"insert into {table} ({columns}) values (%s {', %s' * (len(values) - 1)})"
        )
        insert_command = self.cursor.mogrify(insert_command_string, values)
        try:
            self.cursor.execute(insert_command)
            self.conn.commit()
        except Exception as e:
            logger.info("Exception:", e)
            self.conn.rollback()

    def get_my_projects(self, user_id: int):
        query = """
        SELECT DISTINCT p.id, p.name, p.description, p.created_at
        FROM projects p
        LEFT JOIN tasks t ON t.project_id = p.id
        LEFT JOIN task_assignees ta ON ta.task_id = t.id
        WHERE p.created_by = %s OR ta.user_id = %s
        ORDER BY p.created_at DESC
        """
        self.cursor.execute(query, (user_id, user_id))
        return self.cursor.fetchall()

    def get_my_tasks(self, user_id: int):
        query = """
        SELECT 
            t.id, t.title, t.description, t.status, 
            t.created_at, t.due_date,
            p.name AS project_name,
            u.username AS created_by
        FROM tasks t
        JOIN task_assignees ta ON ta.task_id = t.id
        LEFT JOIN projects p ON t.project_id = p.id
        LEFT JOIN users u ON t.created_by = u.id
        WHERE ta.user_id = %s
        ORDER BY t.created_at DESC
        """
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()

    def assign_task(self, task_id: int, user_id: int):
        query = """
        INSERT INTO task_assignees (task_id, user_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """
        self.cursor.execute(query, (task_id, user_id))
        self.conn.commit()

    def add_task_comment(self, task_id: int, user_id: int, message: str):
        query = """
        INSERT INTO task_comments (task_id, user_id, message)
        VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (task_id, user_id, message))
        self.conn.commit()

    def get_task_comments(self, task_id: int):
        query = """
        SELECT c.message, c.created_at, u.username
        FROM task_comments c
        LEFT JOIN users u ON u.id = c.user_id
        WHERE c.task_id = %s
        ORDER BY c.created_at ASC
        """
        self.cursor.execute(query, (task_id,))
        return self.cursor.fetchall()

    def create_project(self, name: str, description: str, created_by: int):
        query = """
        INSERT INTO projects (name, description, created_by)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        self.cursor.execute(query, (name, description, created_by))
        project_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return project_id
