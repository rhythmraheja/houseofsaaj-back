from typing import List, Optional
from pydantic import BaseModel, HttpUrl, constr

class TagBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=50)

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int

    class Config:
        orm_mode = True

class CategoryBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=50)

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        orm_mode = True

class ProductImageBase(BaseModel):
    url: HttpUrl

class ProductImageCreate(ProductImageBase):
    pass

class ProductImage(ProductImageBase):
    id: int

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=100)
    description: constr(strip_whitespace=True, min_length=1, max_length=300)
    price: float
    discount: Optional[int] = 0
    category_id: int
    tags: List[int] = []

class ProductCreate(ProductBase):
    images: List[ProductImageCreate] = []

class ProductUpdate(ProductBase):
    images: Optional[List[ProductImageCreate]] = None

class Product(ProductBase):
    id: int
    category: Category
    tags: List[Tag] = []
    images: List[ProductImage] = []

    class Config:
        orm_mode = True
