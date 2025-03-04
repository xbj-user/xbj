from app import app, db, User, Product, CartItem
import time
from sqlalchemy.exc import OperationalError

def check_database_data(max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            print(f"\n尝试连接数据库 (尝试 {attempt + 1}/{max_retries})...")
            
            print("\n1. 用户数据：")
            users = User.query.all()
            if users:
                for user in users:
                    print(f"用户名: {user.username}, 注册时间: {user.register_time}")
            else:
                print("没有找到用户数据")

            print("\n2. 商品数据：")
            products = Product.query.all()
            if products:
                for product in products:
                    print(f"商品ID: {product.id}, 名称: {product.name}, 价格: {product.price}, 库存: {product.stock}")
            else:
                print("没有找到商品数据")

            print("\n3. 购物车数据：")
            cart_items = CartItem.query.all()
            if cart_items:
                for item in cart_items:
                    print(f"用户: {item.username}, 商品ID: {item.product_id}, 数量: {item.quantity}")
            else:
                print("没有找到购物车数据")
            
            print("\n✅ 数据库连接和查询成功！")
            break
            
        except OperationalError as e:
            print(f"\n❌ 数据库连接错误 (尝试 {attempt + 1}/{max_retries}):")
            print(str(e))
            
            if attempt < max_retries - 1:
                print(f"\n等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print("\n❌ 达到最大重试次数，无法连接到数据库。")
                raise

if __name__ == '__main__':
    with app.app_context():
        check_database_data() 