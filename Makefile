
load_dump:
	cat dump.sql | docker exec -i db_cp-db-blog-1 psql postgres -U postgres