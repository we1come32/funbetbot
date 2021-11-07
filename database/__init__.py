import asyncio

from loguru import logger
import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_mixins import AllFeaturesMixin
from sqlalchemy_mixins.timestamp import TimestampsMixin

import config

logger = logger.bind(module="DATABASE")

# Объявление основного класса
Base = declarative_base()


class BaseModel(Base, AllFeaturesMixin, TimestampsMixin):
    __abstract__ = True
    pass


def setup():
    # Создание моделей
    from . import models

    memory = "sqllite:///:memory:"
    connector = config.DATABASE
    if connector is memory:
        logger.warning('База данных не установлена. Включено сохранение в оперативную память БЕЗ СОХРАНЕНИЯ В '
                       'ПОСТОЯННУЮ ПАМЯТЬ')
    # Создание подключения к файлу
    logger.debug(f"Подключаемся к базе данных {connector!r}")
    engine = sa.create_engine(connector, echo=False)
    logger.debug(f"Создаем сессию...")
    session = scoped_session(sessionmaker(bind=engine, autocommit=True))
    logger.debug(f"Сессия создана")
    Base.metadata.create_all(engine)
    logger.debug(f"Таблицы базы данных созданы")
    BaseModel.set_session(session)
    logger.debug(f"База данных настроена и готова работать")

