from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

engine = create_engine(
    f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5433/online_restaurant",
    echo=True,
)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Users(Base, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(50), unique=True)
