from app import app, db, User, Product, CartItem
from datetime import datetime
import os
import sys

def test_database():
    """测试数据库连接和基本操作"""
    try:
        with app.app_context():
            # 测试数据库连接
            db.engine.connect()
            print("✅ 数据库连接成功")
            
            # 测试创建表
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 测试用户操作
            test_user = User(username='test_user', password='test123')
            db.session.add(test_user)
            db.session.commit()
            print("✅ 用户创建成功")
            
            # 测试商品操作
            test_product = Product(
                name='测试商品',
                price=99.99,
                description='这是一个测试商品',
                stock=10
            )
            db.session.add(test_product)
            db.session.commit()
            print("✅ 商品创建成功")
            
            # 测试购物车操作
            test_cart = CartItem(
                username='test_user',
                product_id=test_product.id,
                quantity=1
            )
            db.session.add(test_cart)
            db.session.commit()
            print("✅ 购物车项目创建成功")
            
            # 清理测试数据
            db.session.delete(test_cart)
            db.session.delete(test_product)
            db.session.delete(test_user)
            db.session.commit()
            print("✅ 测试数据清理成功")
            
            print("\n所有数据库测试通过！")
            
    except Exception as e:
        print(f"❌ 测试失败：{str(e)}")
        sys.exit(1)

def test_routes():
    """测试基本路由"""
    client = app.test_client()
    
    try:
        # 测试首页
        response = client.get('/')
        assert response.status_code == 200
        print("✅ 首页访问成功")
        
        # 测试登录页面
        response = client.get('/login')
        assert response.status_code == 200
        print("✅ 登录页面访问成功")
        
        # 测试注册页面
        response = client.get('/register')
        assert response.status_code == 200
        print("✅ 注册页面访问成功")
        
        # 测试管理员登录页面
        response = client.get('/admin_login')
        assert response.status_code == 200
        print("✅ 管理员登录页面访问成功")
        
        print("\n所有路由测试通过！")
        
    except Exception as e:
        print(f"❌ 路由测试失败：{str(e)}")
        sys.exit(1)

def test_static_files():
    """测试静态文件目录"""
    try:
        # 检查必要的目录是否存在
        assert os.path.exists('static/images')
        print("✅ 静态文件目录检查通过")
        
        # 检查错误页面是否存在
        assert os.path.exists('templates/404.html')
        assert os.path.exists('templates/500.html')
        print("✅ 错误页面检查通过")
        
        print("\n所有静态文件检查通过！")
        
    except Exception as e:
        print(f"❌ 静态文件检查失败：{str(e)}")
        sys.exit(1)

def main():
    print("开始测试应用...\n")
    
    # 运行所有测试
    test_database()
    test_routes()
    test_static_files()
    
    print("\n所有测试完成！应用可以正常部署。")

if __name__ == "__main__":
    main() 