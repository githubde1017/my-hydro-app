# D:\00_Project\my-hydro-app\backend\init_db.py

from app import app, db

def initialize_database():
    with app.app_context():
        print("正在創建資料庫表...")
        db.create_all()
        print("資料庫表創建完成或已存在。")

if __name__ == '__main__':
    initialize_database()