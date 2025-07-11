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
