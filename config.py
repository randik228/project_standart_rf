import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'standart-rf-demo-2024-secret-key')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "standart_rf.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB