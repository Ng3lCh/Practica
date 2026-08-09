import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambia_esto_por_una_clave_secreta_larga")

    DB_USER = "root"
    DB_PASSWORD = ""
    DB_HOST = "localhost"
    DB_NAME = "oneparfum_db"

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False