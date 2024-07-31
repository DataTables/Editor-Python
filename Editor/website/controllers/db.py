# Note: Need modules
#   pymysql - mysql
#   psycopg2-binary - postgres

# sql server
#   mssql pyodbc - sql server


from sqlalchemy import create_engine

db_config = {
    "type": "sqlite",
    "user": "",
    "password": "",
    "host": "localhost",
    "port": "",
    "db": "/home/colin/temp/editor.db"
}

# db_config = {
#     "type": "mysql+pymysql",
#     "user": "sa",
#     "password": "Pa55word123.",
#     # "host": "192.168.234.234",
#     "host": "192.168.0.59",
#     "port": "3306",
#     "db": "test"
# }

# db_config = {
#     "type": "postgresql+psycopg2",
#     "user": "sa",
#     "password": "Pa55word123.",
#     # "host": "192.168.234.234",
#     "host": "192.168.0.59",
#     "port": "5432",
#     "db": "test"
# }

# docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Pa55word123." -p 1433:1433 -d mcr.microsoft.com/mssql/server:2019-latest
# db_config = {
#     "type": "mssql+pyodbc",
#     "user": "sa",
#     "password": "Pa55word123.",
#     "host": "localhost",
#     "port": "1433",
#     "db": "test"
# }

# oracle


if db_config["type"] == "sqlite":
    connection_string = f"{db_config['type']}:///{db_config['db']}"
elif db_config["type"] in ["mysql+pymysql", "postgresql", "postgresql+psycopg2"]:
    connection_string = f"{db_config['type']}://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"
elif db_config["type"] == "mssql+pyodbc":
    connection_string = (
        f"mssql+pyodbc://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}?"
        f"driver=ODBC+Driver+17+for+SQL+Server"
    )
elif db_config["type"] == "oracle+cx_oracle":
    connection_string = (
        f"oracle+cx_oracle://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/"
        f"?service_name={db_config['db']}"
    )    
else:
    raise Exception("Unknown connection type")

db = create_engine(connection_string, echo=True)
