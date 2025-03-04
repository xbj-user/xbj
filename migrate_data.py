from app import app, db, User, Product, CartItem
import json
from datetime import datetime

def migrate_data():
    print("开始数据迁移...")
    
    # 迁移用户数据
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
            for username, user_info in users_data.items():
                # 检查用户是否已存在
                if not User.query.filter_by(username=username).first():
                    user = User(
                        username=username,
                        password=user_info['password'],
                        register_time=datetime.strptime(user_info['register_time'], '%Y-%m-%d')
                    )
                    db.session.add(user)
            print("用户数据迁移完成")
    except FileNotFoundError:
        print("未找到用户数据文件")

    # 迁移商品数据
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            products_data = json.load(f)
            for product_data in products_data:
                # 检查商品是否已存在
                if not Product.query.filter_by(name=product_data['name']).first():
                    product = Product(
                        name=product_data['name'],
                        price=float(product_data['price']),
                        description=product_data.get('description', ''),
                        image_url=product_data.get('image_url', ''),
                        stock=int(product_data.get('stock', 0))
                    )
                    db.session.add(product)
            print("商品数据迁移完成")
    except FileNotFoundError:
        print("未找到商品数据文件")

    # 保存所有更改
    try:
        db.session.commit()
        print("所有数据迁移成功！")
    except Exception as e:
        db.session.rollback()
        print(f"迁移过程中发生错误: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        migrate_data() 