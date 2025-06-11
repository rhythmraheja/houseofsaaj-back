from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship

from .database import Base

# Association table for many-to-many Product <-> Tag
product_tag = Table(
    'product_tag',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
)

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)

    products = relationship('Product', back_populates='category', cascade="all, delete")

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)

    products = relationship('Product', secondary=product_tag, back_populates='tags')

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(300))
    price = Column(Float)
    discount = Column(Integer, default=0)

    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='products')

    tags = relationship('Tag', secondary=product_tag, back_populates='products')

    images = relationship('ProductImage', back_populates='product', cascade="all, delete")

class ProductImage(Base):
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(200))
    product_id = Column(Integer, ForeignKey('products.id'))

    product = relationship('Product', back_populates='images')
