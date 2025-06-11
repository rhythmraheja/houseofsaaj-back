from sqlalchemy.orm import Session
from typing import List, Optional

from . import models, schemas

# Categories
def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_category_by_name(db: Session, name: str) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.name == name).first()

def get_categories(db: Session) -> List[models.Category]:
    return db.query(models.Category).order_by(models.Category.name).all()

def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int) -> bool:
    cat = get_category(db, category_id)
    if cat:
        db.delete(cat)
        db.commit()
        return True
    return False

# Tags
def get_tag(db: Session, tag_id: int) -> Optional[models.Tag]:
    return db.query(models.Tag).filter(models.Tag.id == tag_id).first()

def get_tag_by_name(db: Session, name: str) -> Optional[models.Tag]:
    return db.query(models.Tag).filter(models.Tag.name == name).first()

def get_tags(db: Session) -> List[models.Tag]:
    return db.query(models.Tag).order_by(models.Tag.name).all()

def create_tag(db: Session, tag: schemas.TagCreate) -> models.Tag:
    db_tag = models.Tag(name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def delete_tag(db: Session, tag_id: int) -> bool:
    tag = get_tag(db, tag_id)
    if tag:
        db.delete(tag)
        db.commit()
        return True
    return False

# Products
def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[models.Product]:
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    db_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        discount=product.discount,
        category_id=product.category_id,
    )
    # Add tags if any exist
    if product.tags:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(product.tags)).all()
        db_product.tags = tags
    # Add images
    for image in product.images:
        db_product.images.append(models.ProductImage(url=image.url))
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate) -> Optional[models.Product]:
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    db_product.name = product_update.name
    db_product.description = product_update.description
    db_product.price = product_update.price
    db_product.discount = product_update.discount
    db_product.category_id = product_update.category_id
    # update tags if provided
    if product_update.tags is not None:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(product_update.tags)).all()
        db_product.tags = tags
    # Update images if provided (overwrite current images)
    if product_update.images is not None:
        # Delete existing images
        db.query(models.ProductImage).filter(models.ProductImage.product_id == product_id).delete()
        db_product.images = [models.ProductImage(url=img.url) for img in product_update.images]
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> bool:
    product = get_product(db, product_id)
    if product:
        db.delete(product)
        db.commit()
        return True
    return False
