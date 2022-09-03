from pymfdata.rdb.mapper import Base
from sqlalchemy import BigInteger, Column, String, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship, composite
from typing import List, Union


class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Union[int, Column] = Column(BigInteger, primary_key=True, autoincrement=True)
    name: Union[str, Column] = Column(String(100), nullable=False)
    overseas_exchange: Union[str, Column] = Column(String(100), nullable=False)
    domestic_exchange: Union[str, Column] = Column(String(100), nullable=False)
    coin: Union[str, Column] = Column(String(100), nullable=False)
    trade_size: Union[float, Column] = Column(Float, nullable=False)
    amount: Union[float, Column] = Column(Float, nullable=False)
    desc: Union[str, Column] = Column(String(100), nullable=False)
    user_id: Union[int, Column] = Column(ForeignKey('user.id', ondelete="RESTRICT"), primary_key=True)

    # @property
    # def book_ids(self) -> List[AuthorBookEntity]:
    #     return self.r_book_ids
    #
    # @book_ids.setter
    # def book_ids(self, books: List[int]):


