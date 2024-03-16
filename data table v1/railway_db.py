from sqlalchemy import create_engine
from sqlalchemy import text


engine = create_engine(
    "mysql+mysqlconnector://root:6544Dd5HFeh4acBeDCbg1cde2H4e6CgC@roundhouse.proxy.rlwy.net:34181/railway",
    echo=True,
)


def create_table():
    sql = text("CREATE TABLE hello(id text) ")
    with engine.connect() as con:
        try:
            con.execute(sql)
            print("Table created successfully!")
        except Exception as e:
            print(e)
            print("Failed to create table.")


def delete_table():
    sql = text("DROP TABLE hello")
    with engine.connect() as con:
        try:
            con.execute(sql)
            print("Table deleted successfully!")
        except Exception as e:
            print(e)
            print("Failed to delete table.")


create_table()
# delete_table()
