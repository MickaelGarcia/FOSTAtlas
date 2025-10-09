"""Database object module."""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from atlas_db.models import Base


_db_path = f"sqlite:///{os.path.dirname(__file__)}/test_alchemy.db"


class Db:
    """Database Innit."""

    def __init__(self):
        engine = create_engine(_db_path)
        self.Session = sessionmaker(engine)
        Base.metadata.create_all(bind=engine)
        self._session = None


class DbCommitContext(Db):
    """Database add object context."""

    def __enter__(self):
        self._session = self.Session()
        return self._session

    def __exit__(self, *args, **kwargs):
        self._session.commit()
        self._session.close()


class DbQueryContext(Db):
    """Database add object context."""

    def __enter__(self):
        self._session = self.Session()
        return self._session

    def __exit__(self, *args, **kwargs):
        self._session.close()
