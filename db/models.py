from peewee import *
from playhouse.pool import PooledPostgresqlDatabase

db = PooledPostgresqlDatabase('tada', user='postgres', password='admin', host='localhost', port=5432, max_connections=8, stale_timeout=60)


class BaseModel(Model):
    class Meta:
        database = db


class Contest(BaseModel):
    starts = DateField()
    ends = DateField()
    publicCanVote = BooleanField(default=False)


class User(BaseModel):
    telegramId = TextField(unique=True)
    isAdmin = BooleanField(default=False)


class Submission(BaseModel):
    filename = TextField()
    title = TextField()
    link = TextField()
    nsfw = BooleanField()
    contentWarnings = TextField()
    at = TextField()
    author = TextField()
    contest = ForeignKeyField(Contest, backref='submissions')
    user = ForeignKeyField(User, backref='submissions')
    # isPending = BooleanField(default=True)


class SupportMessage(BaseModel):
    fromUserId = TextField()
    fromMsgId = TextField(unique=True)
    adminChatMsgId = TextField(unique=True)


class Theme(BaseModel):
    name = TextField()
    contest = ForeignKeyField(Contest, backref='themes')


db.connect()
db.create_tables([Contest, User, Submission, Theme, SupportMessage])
db.close()