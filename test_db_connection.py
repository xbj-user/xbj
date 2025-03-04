from dotenv import load_dotenv
import os
import sys
from sqlalchemy import create_engine, text

def test_database_connection():
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取数据库URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("错误：未设置DATABASE_URL环境变量")
            sys.exit(1)
            
        # 确保使用正确的URL格式
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
            
        # 添加SSL参数
        if '?' in database_url:
            database_url += '&ssl=true'
        else:
            database_url += '?ssl=true'
            
        print(f"正在尝试连接到数据库...")
        print(f"连接URL: {database_url}")
            
        # 创建数据库引擎
        engine = create_engine(database_url, connect_args={'ssl_context': 'require'})
        
        # 尝试连接并执行简单查询
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            print("数据库连接测试成功！")
            print(f"已成功连接到数据库：{database_url}")
            
    except Exception as e:
        print(f"数据库连接测试失败！错误信息：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_database_connection() 