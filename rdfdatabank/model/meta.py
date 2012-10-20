# -*- coding: utf-8 -*-

"""Creates SQLAlchemy Metadata and Session object"""
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

__all__ = ['engine', 'Session', 'metadata']

# SQLAlchemy database engine.  Updated by model.init_model()
engine = None

# SQLAlchemy session manager. Updated by model.init_model()
Session = scoped_session(sessionmaker())

#metadata = MetaData()
Base = declarative_base()
metadata = Base.metadata

