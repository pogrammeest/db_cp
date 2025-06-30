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