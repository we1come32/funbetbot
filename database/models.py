import datetime

import sqlalchemy as sa
import sqlalchemy.orm

from . import BaseModel


class TGUser(BaseModel):
    __tablename__ = 'tg_user'
    __repr_attrs__ = ['id']

    id = sa.Column(sa.Integer, primary_key=True)
    status = sa.Column(sa.Integer, default=0)
    balance = sa.Column(sa.Integer, default=1000)


class Category(BaseModel):
    __tablename__ = 'bet_category'
    __repr_attrs__ = ['id']

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(20), default='')
    subcategories = sa.orm.relationship('SubCategory')


class SubCategory(BaseModel):
    __tablename__ = 'bet_subcategory'
    __repr_attrs__ = ['id']

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(20), default='')
    category = sa.Column(sa.ForeignKey('bet_category.id'))
    tournaments = sa.orm.relationship('Tournament')


class Tournament(BaseModel):
    __tablename__ = 'bet_tournaments'
    __repr_attrs__ = ['id']

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(20), default='')
    subcategory = sa.Column(sa.ForeignKey('bet_subcategory.id'))
    events = sa.orm.relationship('Event')


class Event(BaseModel):
    __tablename__ = 'bet_events'
    __repr_attrs__ = ['id']

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(20), default='')
    tournament = sa.Column(sa.ForeignKey('bet_tournaments.id'))
    teams = sa.orm.relationship('GameTeam')


class Team(BaseModel):
    __tablename__ = 'bet_teams'
    __repr_attrs__ = ['id']

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(20), default='')
    subcategory = sa.Column(sa.ForeignKey('bet_events.id'))
    value = sa.Column(sa.Float, default=1.0)
    start_time = sa.Column(sa.Time, default=datetime.datetime.now)
    bets = sa.orm.relationship('Bet')


class Bet(BaseModel):
    __tablename__ = 'bet_bets'
    __repr_attrs__ = ['id']

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    value = sa.Column(sa.Float)
    user = sa.Column(sa.ForeignKey('tg_user.id'))
    bet = sa.Column(sa.ForeignKey('bet_teams.id'))
