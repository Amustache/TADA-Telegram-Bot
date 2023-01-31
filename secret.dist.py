TOKEN = "1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
ADMINS_GROUPCHAT = -1
DUMP_GROUPCHAT = -1

# Select you database
from peewee import SqliteDatabase


DB = SqliteDatabase("./db/main.db")

# from playhouse.pool import PooledPostgresqlDatabase
# DB_DB = "tada"
# DB_USER = "postgres"
# DB_PW = "hunter2"
# DB_HOST = "localhost"
# DB_PORT = 5432
# DB = PooledPostgresqlDatabase(
#     DB_DB, user=DB_USER, password=DB_PW, host=DB_HOST, port=DB_PORT, max_connections=8, stale_timeout=60
# )
