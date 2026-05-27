from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.dialects.postgresql import JSONB


engine = create_engine(
    "sqlite:///database.db",
    echo=True,
)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    def create_db(self):
        Base.metadata.create_all(engine)

    def drop_db(self):
        Base.metadata.drop_all(engine)


class Users(Base, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(50), unique=True)

    orders = relationship(
        "Orders", foreign_keys="Orders.user_id", back_populates="user"
    )


class Menu(Base):
    __tablename__ = "menu"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    image: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
    time: Mapped[int] = mapped_column()
    cost: Mapped[int] = mapped_column(nullable=False)


class Orders(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_list: Mapped[str] = mapped_column(String)
    order_time: Mapped[datetime] = mapped_column(DateTime)

    user = relationship("Users", foreign_keys="Orders.user_id", back_populates="orders")


if __name__ == "__main__":
    base = Base()
    base.create_db()

    item = Menu(
        name="Спагетти аматричана",
        image="https://i0.wp.com/www.vsyasol.com/wp-content/uploads/2016/10/IMG_1902.jpg?resize=630%2C300&ssl=1",
        description="Имя этой пасте дал старинный городок Аматриче в регионе Абруццо, о котором в последнее время чаще говорят не как о родине знаменитого блюда, а как о жертве разрушительного землетрясения.",
        time=10,
        cost=8,
    )
    with Session() as cursor:
        cursor.add(item)
        cursor.commit()
