import re

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
