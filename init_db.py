from app import app, db
import sys

def init_database():
    try:
        with app.app_context():
            # 尝试连接数据库
            db.engine.connect()
            print("✅ 成功连接到数据库")
            
            # 创建所有数据库表
            db.create_all()
            print("✅ 成功创建所有数据库表")
            
            print("\n数据库初始化完成！")
    except Exception as e:
        print(f"❌ 初始化数据库时出错：\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_database() 