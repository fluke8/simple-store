import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

# логирование
logger.add(sys.stderr, level="INFO")

DATABASE_URL = "postgresql://user:password@db:5432/store"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Float, index=True)

app = FastAPI()

# Функция для очистки базы данных
def clear_database():
    logger.info("Clearing database")
    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE;"))
        db.commit()
    except Exception as e:
        logger.error("Error clearing database: {}", e)
        db.rollback()
    finally:
        db.close()

# Применяем очистку базы данных при запуске приложения
clear_database()

Base.metadata.create_all(bind=engine)

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float

class ProductUpdate(BaseModel):
    name: str = None
    description: str = None
    price: float = None

@app.post("/products/", response_model=ProductCreate)
def create_product(product: ProductCreate):
    logger.info("Creating product: {}", product.name)
    db = SessionLocal()
    db_product = Product(name=product.name, description=product.description, price=product.price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    logger.info("Product created: {}", db_product.id)
    return db_product

@app.get("/products/{product_id}", response_model=ProductCreate)
def read_product(product_id: int):
    logger.info("Reading product: {}", product_id)
    db = SessionLocal()
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        logger.warning("Product not found: {}", product_id)
        raise HTTPException(status_code=404, detail="Product not found")
    logger.info("Product read: {}", db_product.id)
    return db_product

@app.put("/products/{product_id}", response_model=ProductCreate)
def update_product(product_id: int, product: ProductUpdate):
    logger.info("Updating product: {}", product_id)
    db = SessionLocal()
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        logger.warning("Product not found: {}", product_id)
        raise HTTPException(status_code=404, detail="Product not found")
    if product.name:
        db_product.name = product.name
    if product.description:
        db_product.description = product.description
    if product.price:
        db_product.price = product.price
    db.commit()
    db.refresh(db_product)
    logger.info("Product updated: {}", db_product.id)
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    logger.info("Deleting product: {}", product_id)
    db = SessionLocal()
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        logger.warning("Product not found: {}", product_id)
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    logger.info("Product deleted: {}", product_id)
    return {"detail": "Product deleted"}
