from configparser import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

configure = ConfigParser()
configure.read('config.ini')


def db_connection(server_alias):
    if server_alias.lower() == "dev":
        db_engine, session = read_dev_db()
        return db_engine, session


def read_dev_db():
    db_host = configure.get('DEV_DB_CONFIG', 'db_host')
    db_username = configure.get('DEV_DB_CONFIG', 'db_username')
    db_password = configure.get('DEV_DB_CONFIG', 'db_password')
    db_port = configure.get('DEV_DB_CONFIG', 'db_port')
    db_name = configure.get('DEV_DB_CONFIG', 'db_name')

    db_engine = create_engine('postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
        db_username, db_password, db_host, db_port, db_name
    ))
    session = Session(db_engine)

    return db_engine, session
