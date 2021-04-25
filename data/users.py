import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True)
    wins = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    defs = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
