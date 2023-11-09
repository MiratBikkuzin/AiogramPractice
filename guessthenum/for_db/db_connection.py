from pymysql import connect, Connection
from pymysql.cursors import DictCursor
from db_data import *


CONNECTION: Connection = connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name,
    port=db_port,
    cursorclass=DictCursor,
    autocommit=True
)