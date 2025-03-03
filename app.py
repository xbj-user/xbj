from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from decimal import Decimal  # 导入 Decimal 模块
from datetime import datetime  # 新增导入 datetime 模块
import os
import json
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

PRODUCTS_FILE = 'products.json'
USERS_FILE = 'users.json'  # 新增用户数据文件

def save_products():
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def load_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_users():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'admin': {'password': '123456', 'register_time': '2025-03-01'}}  # 初始管理员账户

products = load_products()

users = load_users()  # 启动时加载用户数据

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return '用户名或密码错误', 403
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_username_input = request.form['admin_username']
        admin_password_input = request.form['admin_password']
        if admin_username_input == 'admin' and admin_password_input == '123456':
            session['admin'] = admin_username_input
            return redirect(url_for('admin_dashboard'))
        else:
            return '管理员用户名或密码错误', 403
    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not re.match("^[A-Za-z0-9]+$", username):
            error = "用户名只能包含英文字母和数字"
        elif username in users:
            error = "用户名已存在"
        else:
            # 添加注册时间
            users[username] = {
                'password': password,
                'register_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            save_users()  # 保存用户数据
            return redirect(url_for('login'))
            
    return render_template('register.html', error=error)

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        
        if 'image' not in request.files:
            return '没有文件上传'
        image = request.files['image']
        
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f"images/{filename}"
        else:
            return '无效的文件格式'
        
        product_id = len(products) + 1
        new_product = {'id': product_id, 'name': name, 'price': price, 'description': description, 'image_url': image_url, 'stock': stock}
        products.append(new_product)
        save_products()

        return redirect(url_for('admin_dashboard'))

    return render_template('admin_dashboard.html', products=products, users=users)

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    filtered_products = [p for p in products if search_query.lower() in p['name'].lower()]
    return render_template('index.html', products=filtered_products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return render_template('product_detail.html', product=product)
    return '产品未找到', 404

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if 'cart' not in session:
        session['cart'] = []
    
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        found = False
        for item in session['cart']:
            if item['product']['id'] == product_id:
                item['quantity'] += 1
                found = True
                break
        if not found:
            session['cart'].append({'product': product, 'quantity': 1})
        session.modified = True
    return redirect(url_for('cart_view'))

@app.route('/cart')
def cart_view():
    if 'cart' not in session:
        session['cart'] = []
    
    # 使用 Decimal 计算总价，确保精度
    total_price = sum(Decimal(str(item['product']['price'])) * Decimal(str(item['quantity'])) for item in session['cart'])
    total_price = float(total_price)  # 转换为浮点数以便渲染模板
    return render_template('cart.html', cart=session['cart'], total_price=total_price)

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    action = request.args.get('action', 'reduce')
    
    for index, item in enumerate(session['cart']):
        if item['product']['id'] == product_id:
            if action == 'remove' or item['quantity'] <= 1:
                session['cart'].pop(index)
            else:
                item['quantity'] -= 1
            session.modified = True
            break
    return redirect(url_for('cart_view'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        session.pop('cart', None)
        return redirect(url_for('index'))
    
    if 'cart' not in session:
        session['cart'] = []
    
    # 使用 Decimal 计算总价，确保精度
    total_price = sum(Decimal(str(item['product']['price'])) * Decimal(str(item['quantity'])) for item in session['cart'])
    total_price = float(total_price)  # 转换为浮点数以便渲染模板
    return render_template('checkout.html', cart=session['cart'], total_price=total_price)

@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if 'admin' not in session:
        return jsonify({'error': '无权操作'}), 403

    global products
    products = [p for p in products if p['id'] != product_id]
    save_products()
    return jsonify({'success': True}), 200

# 新增编辑商品的路由
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return '商品未找到', 404

    if request.method == 'POST':
        # 更新商品信息
        product['name'] = request.form['name']
        product['price'] = float(request.form['price'])
        product['description'] = request.form['description']
        product['stock'] = int(request.form['stock'])

        # 处理图片上传
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product['image_url'] = f"images/{filename}"

        save_products()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_product.html', product=product)

#删除用户路由
@app.route('/delete_user/<username>', methods=['DELETE'])
def delete_user(username):
    if 'admin' not in session:
        return jsonify({'error': '无权操作'}), 403

    if username not in users:
        return jsonify({'error': '用户不存在'}), 404

    # 删除用户
    del users[username]
    save_users()  # 保存更新后的用户数据

    return jsonify({'success': True}), 200

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session.pop('cart', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)