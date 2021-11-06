import sqlalchemy as sa
import sqlalchemy.orm

from . import BaseModel


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['id']

    id = sa.Column(sa.Integer, primary_key=True)
    status = sa.Column(sa.Integer, default=0)
    balance = sa.Column(sa.Integer, default=1000)

