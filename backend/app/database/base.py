from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.x Declarative Base.
    All ORM models across the application will inherit from this base class.
    """
    pass
