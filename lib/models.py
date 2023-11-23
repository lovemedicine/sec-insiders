import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True)
    sec_cik: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(50))
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"Company(id={self.id!r}, name={self.name!r}, ticker={self.ticker!r}, sec_cik={self.sec_cik!r})"

class Person(Base):
    __tablename__ = "people"
    id: Mapped[int] = mapped_column(primary_key=True)
    sec_cik: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(60))
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"Person(id={self.id!r}, name={self.name!r}, sec_cik={self.sec_cik!r})"


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    company: Mapped["Company"] = relationship(back_populates="transactions")
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    person: Mapped["Person"] = relationship(back_populates="transactions")
    date: Mapped[datetime.date] = mapped_column(index=True)
    filing_date: Mapped[datetime.date]
    direction: Mapped[str] = mapped_column(String(10)) # 'purchase' or 'sale'
    security_type: Mapped[str] = mapped_column(String(10)) # 'stock' or 'option'
    shares: Mapped[int]
    price: Mapped[float]
    is_director: Mapped[bool]
    is_executive: Mapped[bool]
    is_owner: Mapped[bool]
    person_title: Mapped[Optional[str]] = mapped_column(String(30))
    is_direct: Mapped[bool]
    accession_no: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
