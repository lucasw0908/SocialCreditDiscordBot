from sqlalchemy import Column, Integer, String
from typing import Literal

from bot.models import db


class Item(db):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True)
    description = Column(String(256))
    price = Column(Integer)
    type = Column(String(16))
    
    def __init__(self, name: str, description: str, price: int, type: Literal["custom", "item", "character", "test"]="custom"):
        self.name = name
        self.description = description
        self.price = price
        self.type = type
        
    
    def __repr__(self):
        return f"<Item(name={self.name}, price={self.price})>"