CREATE TABLE public.admins_commands (
    id_command integer NOT NULL,
    headline character varying(50),
    description character varying(100)
);
CREATE TABLE public.all_products (
    id integer NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name character varying(50),
    price integer,
    description character varying(100),
    stat character varying(50),
    weight integer
);
CREATE TABLE public.gamers (
    id integer NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name character varying(50) NOT NULL,
    email character varying(50),
    password character varying(50) NOT NULL,
    health integer DEFAULT 100,
    mana integer DEFAULT 100,
    last_online_time timestamp without time zone DEFAULT now(),
    is_admin boolean DEFAULT false
);
CREATE TABLE public.inventory (
    id_user integer NOT NULL,
    max_weight integer,
    list_items character varying(50),
    FOREIGN KEY(id_user) REFERENCES gamers(id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE TABLE public."position" (
    map_name character varying(50),
    user_id integer NOT NULL,
    x double precision,
    y double precision,
    z double precision,
    FOREIGN KEY(user_id) REFERENCES gamers(id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE TABLE public.shop (
    todays_products character varying(50),
    id_products integer NOT NULL,
    price integer,
    date timestamp without time zone
    FOREIGN KEY(id_products) REFERENCES all_products(id) ON UPDATE CASCADE ON DELETE CASCADE
);
 
Класс работы с СУБД:
import psycopg2
import prettytable


class WorkingWithDataBase():
    def __init__(self):
        self.conn = psycopg2.connect(
            user='postgres',
            password='admin',
            port='5432',
            database='trzbd_DB'
        )
        self.cursor = self.conn.cursor()

    def select_many_rows(self, table, columns='*', condition=''):
        select_many_rows_command = f"select {columns} from {table} where {condition}"
        self.cursor.execute(select_many_rows_command)

        return self.cursor.fetchall()

    def select_one_row(self, table, columns='*', condition=""):
        select_one_row_command = f"select {columns} from {table} where {condition}"
        self.cursor.execute(select_one_row_command)

        return self.cursor.fetchone()

    def select_all_rows(self, columns='*', table='table'):
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
            return exc

    def get_table_name(self):
        get_table_name_command = f"SELECT table_name FROM information_schema.tables  where table_schema='public' ORDER BY table_name;"
        self.cursor.execute(get_table_name_command)
        data = []
        for table in self.cursor.fetchall():
            data.append(table[0])
        return data

    def update(self, table, set_string="", condition=""):  # UPDATE weather SET temp_lo = temp_lo+1, temp_hi = temp_lo+15, prcp = DEFAULT WHERE city = 'San Francisco' AND date = '2003-07-03'

        update_command = f"UPDATE {table} SET {set_string} WHERE {condition}"
        self.cursor.execute(update_command)
        self.conn.commit()


    def delete(self, table, condition=""):  # DELETE FROM films WHERE kind <> 'Musical';

        delete_command = f"DELETE FROM {table} WHERE {condition}"
        self.cursor.execute(delete_command)
        self.conn.commit()


    def insert(self, table='', columns='', values=()):
        insert_command_string = f"insert into {table} ({columns}) values (%s {', %s' * (len(values) - 1)})"
        insert_command = self.cursor.mogrify(insert_command_string, values)
        try:
            self.cursor.execute(insert_command)
            self.conn.commit()
        except Exception as e:
            print('Exception:', e)
            self.conn.rollback()

