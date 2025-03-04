from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from decimal import Decimal  # 导入 Decimal 模块
from datetime import datetime, timedelta  # 新增导入 datetime 模块
import os
from dotenv import load_dotenv  # 添加这行
import json
import re
from urllib.parse import urlparse, parse_qs
import logging
from logging.handlers import RotatingFileHandler

# 加载环境变量
load_dotenv()  # 添加这行

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# 配置日志
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('应用启动')

# 数据库配置
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError("未设置 DATABASE_URL 环境变量")

# 确保使用 pg8000 驱动并添加 SSL 参数
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
elif database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)

# 添加 SSL 参数到 URL
if '?' in database_url:
    database_url += '&sslmode=require'
else:
    database_url += '?sslmode=require'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}

# 添加安全配置
app.config['SESSION_COOKIE_SECURE'] = True  # 只通过HTTPS发送cookie
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问cookie
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # session过期时间
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

db = SQLAlchemy(app)

# 用户模型
class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(120), nullable=False)
    register_time = db.Column(db.DateTime, default=datetime.utcnow)

# 商品模型
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    stock = db.Column(db.Integer, default=0)

# 购物车项目模型
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('users.username'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product')

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

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
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
        elif User.query.filter_by(username=username).first():
            error = "用户名已存在"
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
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
        
        new_product = Product(
            name=name,
            price=price,
            description=description,
            image_url=image_url,
            stock=stock
        )
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('admin_dashboard'))

    products = Product.query.all()
    users = User.query.all()
    return render_template('admin_dashboard.html', products=products, users=users)

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    if search_query:
        filtered_products = Product.query.filter(Product.name.ilike(f'%{search_query}%')).all()
    else:
        filtered_products = Product.query.all()
    return render_template('index.html', products=filtered_products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    username = session['username']
    
    cart_item = CartItem.query.filter_by(
        username=username,
        product_id=product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(
            username=username,
            product_id=product_id,
            quantity=1
        )
        db.session.add(cart_item)
    
    db.session.commit()
    return redirect(url_for('cart_view'))

@app.route('/cart')
def cart_view():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    cart_items = CartItem.query.filter_by(username=session['username']).all()
    total_price = sum(Decimal(str(item.product.price)) * Decimal(str(item.quantity)) for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=float(total_price))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    action = request.args.get('action', 'reduce')
    cart_item = CartItem.query.filter_by(
        username=session['username'],
        product_id=product_id
    ).first_or_404()
    
    if action == 'remove' or cart_item.quantity <= 1:
        db.session.delete(cart_item)
    else:
        cart_item.quantity -= 1
    
    db.session.commit()
    return redirect(url_for('cart_view'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    cart_items = CartItem.query.filter_by(username=session['username']).all()
    
    if request.method == 'POST':
        # 清空购物车
        CartItem.query.filter_by(username=session['username']).delete()
        db.session.commit()
        return redirect(url_for('index'))
    
    total_price = sum(Decimal(str(item.product.price)) * Decimal(str(item.quantity)) for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total_price=float(total_price))

@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if 'admin' not in session:
        return jsonify({'error': '无权操作'}), 403

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True}), 200

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.description = request.form['description']
        product.stock = int(request.form['stock'])

        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image_url = f"images/{filename}"

        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_product.html', product=product)

@app.route('/delete_user/<username>', methods=['DELETE'])
def delete_user(username):
    if 'admin' not in session:
        return jsonify({'error': '无权操作'}), 403

    user = User.query.get(username)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True}), 200
    return jsonify({'error': '用户不存在'}), 404

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session.pop('cart', None)
    return redirect(url_for('index'))

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error('页面未找到: %s', request.url)
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error('服务器错误: %s', error)
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(e):
    app.logger.error('文件太大: %s', request.url)
    return "文件太大", 413

# 请求前处理
@app.before_request
def before_request():
    if not request.is_secure and app.config['SESSION_COOKIE_SECURE']:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# 请求后处理
@app.after_request
def after_request(response):
    app.logger.info('请求完成: %s %s %s', request.method, request.url, response.status)
    return response

if __name__ == '__main__':
    app.run(debug=True)