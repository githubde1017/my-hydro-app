# backend/config.py
class Config:
    # 替換為您的 PostgreSQL 連線資訊
    DB_CONNECT_STRING = "dbname='my_hydro_db' user='postgres' password='admin' host='localhost' port='5432'"
    SECRET_KEY = '16f5b824d3e17ec23499d0b3fcb81963' # 請替換為一個真正安全的隨機字串