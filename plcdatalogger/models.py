from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from config import DataLoggerConfig



class BaseData(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    date_created: datetime = Field(nullable=False, default_factory=datetime.now)


def create_class(config: DataLoggerConfig) -> None:
    pass