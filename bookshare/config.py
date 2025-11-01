from dotenv import load_dotenv
import os

load_dotenv()  # loads variables from .env into environment

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = ".\\bookshare\\static\\images"
    MERCHANT_KEY = os.getenv("MERCHANT_KEY")