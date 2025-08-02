from app import app, db

with app.app_context():
    # 這個指令會根據你的模型（Manhole, Pipeline, CatchmentArea）
    # 在資料庫中創建對應的表格。
    db.create_all()
    print("資料庫表格已成功創建！")