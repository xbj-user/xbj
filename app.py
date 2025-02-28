from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import json  # 新增导入

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于session加密
app.config['UPLOAD_FOLDER'] = 'static/images'  # 图片上传文件夹
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # 允许的文件格式

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 商品数据持久化
PRODUCTS_FILE = 'products.json'

def save_products():
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def load_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # 初始化为空列表

# 加载商品数据
products = load_products()

# 模拟用户数据库
users = {
    'admin': '123456'  # 管理员用户名和密码
}

# 模拟购物车
cart = []

# 检查文件类型
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:  # 如果已经登录，跳转到首页
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return '用户名或密码错误', 403
    return render_template('login.html')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    admin_username_input = request.form['admin_username']
    admin_password_input = request.form['admin_password']
    if admin_username_input == 'admin' and admin_password_input == '123456':  # 管理员用户名和密码
        session['admin'] = admin_username_input  # 设置管理员会话
        return redirect(url_for('admin_dashboard'))  # 登录成功，跳转到后台管理面板
    else:
        return '管理员用户名或密码错误', 403

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:  # 如果没有管理员登录，跳转到登录页面
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        
        # 处理图片上传
        if 'image' not in request.files:
            return '没有文件上传'
        image = request.files['image']
        
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f"images/{filename}"  # 修正图片路径
        else:
            return '无效的文件格式'
        
        # 保存商品数据到产品列表
        product_id = len(products) + 1  # 商品ID
        new_product = {'id': product_id, 'name': name, 'price': price, 'description': description, 'image_url': image_url, 'stock': stock}
        products.append(new_product)
        save_products()  # 保存商品数据到文件

        return redirect(url_for('admin_dashboard'))  # 上传成功后返回后台管理面板

    return render_template('admin_dashboard.html', products=products)

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
    if 'username' not in session:  # 如果没有登录，强制要求登录
        return redirect(url_for('login'))

    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        # 检查商品是否已经在购物车中
        found = False
        for item in cart:
            if item['product']['id'] == product_id:
                item['quantity'] += 1
                found = True
                break
        if not found:
            cart.append({'product': product, 'quantity': 1})
    return redirect(url_for('cart_view'))

@app.route('/cart')
def cart_view():
    total_price = sum(item['product']['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart=cart, total_price=total_price)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        # 处理结算逻辑，提交订单
        return '订单已提交'
    total_price = sum(item['product']['price'] * item['quantity'] for item in cart)
    return render_template('checkout.html', cart=cart, total_price=total_price)

@app.route('/logout')
def logout():
    session.pop('username', None)  # 注销登录状态
    session.pop('admin', None)  # 注销管理员登录状态
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)