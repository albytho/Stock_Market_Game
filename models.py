from peewee import *
import datetime

db = SqliteDatabase('Users.db')

class User(Model):
    name = TextField()
    username = TextField()
    email = TextField()
    password = TextField()
    date = DateTimeField(default = datetime.datetime.now)
    money = float(10000)
    portfolio = {}

    class Meta:
        database = db

def initialize_db():
    db.connect()
    db.create_tables([User], safe = True)
