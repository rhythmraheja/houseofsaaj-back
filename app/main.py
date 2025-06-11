from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid

from . import models, schemas, crud, database

# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="House of Saaj API")

# CORS for react frontend
origins = [
    "https://houseofsaaj-front.onrender.com",  # React default port
    # add your frontend domain if deployed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple admin authentication using API key query param (for demo)
ADMIN_PASSWORD = "admin123"

# Removed the admin_auth function as it's no longer needed

# Static directory for images
IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(IMAGES_DIR, exist_ok=True)

# Mount static files path for images
app.mount("/static/images", StaticFiles(directory=IMAGES_DIR), name="images")

# --- CATEGORY ROUTES ---

@app.get("/categories", response_model=List[schemas.Category])
def list_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)

@app.post("/categories", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    existing = crud.get_category_by_name(db, category.name)
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    return crud.create_category(db, category)

@app.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    success = crud.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return None

# --- TAG ROUTES ---

@app.get("/tags", response_model=List[schemas.Tag])
def list_tags(db: Session = Depends(get_db)):
    return crud.get_tags(db)

@app.post("/tags", response_model=schemas.Tag)
def create_tag(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    existing = crud.get_tag_by_name(db, tag.name)
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")
    return crud.create_tag(db, tag)

@app.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    success = crud.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return None

# --- PRODUCT ROUTES ---

@app.get("/products", response_model=List[schemas.Product])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, password: str = Query(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    # Validate category exists
    category = crud.get_category(db, product.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category does not exist")
    # Validate tag ids exist
    if product.tags:
        tags_in_db = db.query(models.Tag).filter(models.Tag.id.in_(product.tags)).all()
        if len(tags_in_db) != len(product.tags):
            raise HTTPException(status_code=400, detail="One or more tags do not exist")
    return crud.create_product(db, product)

@app.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product_data: schemas.ProductUpdate, password: str = Query(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    # Validate category
    category = crud.get_category(db, product_data.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category does not exist")
    if product_data.tags:
        tags_in_db = db.query(models.Tag).filter(models.Tag.id.in_(product_data.tags)).all()
        if len(tags_in_db) != len(product_data.tags):
            raise HTTPException(status_code=400, detail="One or more tags do not exist")
    product = crud.update_product(db, product_id, product_data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, password: str = Query(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    success = crud.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return None

# --- IMAGE UPLOAD ROUTE ---

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import BackgroundTasks

# Read AWS config from environment variables
import os

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_S3_REGION = os.getenv("AWS_S3_REGION", "us-east-1")  # default region

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION,
)

@app.post("/upload-image")
def upload_image(file: UploadFile = File(...), password: str = Query(...)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Not an image file")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        raise HTTPException(status_code=400, detail="Unsupported image extension")

    unique_filename = f"{uuid.uuid4().hex}{ext}"

    # Debug: Print file details
    print(f"Uploading file: {file.filename}, Content Type: {file.content_type}")

    # Upload to S3
    file.file.seek(0)  # Ensure the file pointer is at the start
    success = upload_file_to_s3(file.file, AWS_S3_BUCKET_NAME, unique_filename, file.content_type)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload image to S3")

    s3_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/{unique_filename}"
    return {"url": s3_url}

def upload_file_to_s3(file_obj, bucket, object_name, content_type):
    try:
        s3_client.upload_fileobj(
            file_obj,
            bucket,
            object_name,
            ExtraArgs={"ACL": "public-read", "ContentType": content_type}
        )
    except (BotoCoreError, ClientError) as e:
        print(f"Error uploading to S3: {e}")
        return False
    return True
