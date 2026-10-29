import os, sqlite3, secrets
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('AURA_DB_PATH', os.path.join(BASE, 'aura.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=2*1024*1024)

SEED = [
 ("Everyday Linen Shirt","AURA STUDIO","Men",1299,1799,"S","#D8C7AD","https://images.unsplash.com/photo-1603252109303-2751441dd157?auto=format&fit=crop&w=900&q=85","Breathable linen-blend shirt for easy everyday styling."),
 ("Relaxed Fit Trousers","AURA STUDIO","Men",1599,2199,"S,M,L,XL","#B7A58D","https://images.unsplash.com/photo-1473966968600-fa801b869a1a?auto=format&fit=crop&w=900&q=85","A clean relaxed silhouette with all-day comfort."),
 ("Minimal Gold Hoops","FORME","Accessories",599,899,"One Size","#C8A45D","https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=900&q=85","A subtle statement for everyday outfits."),
 ("Classic White Sneakers","AURA SPORT","Shoes",1999,2799,"6,7,8,9,10","#F3F0E8","https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85","Versatile low-top sneakers for your daily rotation."),
 ("Structured Shoulder Bag","FORME","Accessories",1799,2499,"One Size","#8B6B54","https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=900&q=85","A polished everyday bag with a timeless shape."),
 ("Soft Knit Top","AURA STUDIO","Women",999,1499,"XS,S,M,L,XL","#D9B5A7","https://images.unsplash.com/photo-1564257577-0a7e7c5a7d4a?auto=format&fit=crop&w=900&q=85","Soft-touch knit with a relaxed, versatile fit."),
 ("Everyday Denim","AURA DENIM","Women",1899,2599,"26,28,30,32,34","#7C8FA5","https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=85","Easy denim made for repeat wear."),
 ("Oversized Cotton Tee","AURA STUDIO","Men",799,1199,"S,M,L,XL","#D6D0C4","https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85","A heavyweight cotton tee with a roomy fit."),
 ("Everyday Crossbody","FORME","Accessories",1199,1699,"One Size","#9D7764","https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=900&q=85","Compact carry with room for your essentials."),
 ("Runner Sneakers","AURA SPORT","Shoes",2299,3199,"6,7,8,9,10","#B6B9B5","https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85","Lightweight everyday sneakers with a sporty edge."),
 ("Everyday Sunglasses","FORME","Accessories",899,1299,"One Size","#51483F","https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=900&q=85","An understated frame that finishes any look."),
 ("Relaxed Summer Dress","AURA STUDIO","Women",1699,2299,"XS,S,M,L,XL","#C8A6A1","https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=900&q=85","An easy warm-weather dress with a fluid drape.")
]

def db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(exc):
    conn = g.pop('db', None)
    if conn is not None: conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT NOT NULL, brand TEXT NOT NULL, category TEXT NOT NULL, price INTEGER NOT NULL, old_price INTEGER NOT NULL DEFAULT 0, sizes TEXT NOT NULL DEFAULT 'One Size', color TEXT NOT NULL DEFAULT '', image TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, order_no TEXT UNIQUE NOT NULL, user_id INTEGER NOT NULL REFERENCES users(id), customer_name TEXT NOT NULL, phone TEXT NOT NULL, address TEXT NOT NULL, city TEXT NOT NULL, pin TEXT NOT NULL, payment_method TEXT NOT NULL DEFAULT 'COD', status TEXT NOT NULL DEFAULT 'Placed', subtotal INTEGER NOT NULL, shipping INTEGER NOT NULL, total INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE, product_id INTEGER, product_name TEXT NOT NULL, size TEXT NOT NULL, qty INTEGER NOT NULL, unit_price INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS wishlist(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, PRIMARY KEY(user_id, product_id));
    ''')
    count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    if count == 0:
        conn.executemany('INSERT INTO products(name,brand,category,price,old_price,sizes,color,image,description) VALUES(?,?,?,?,?,?,?,?,?)', SEED)
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@aura.local').strip().lower()
    admin_password = os.environ.get('ADMIN_PASSWORD', 'ChangeMe123!')
    existing = conn.execute('SELECT id FROM users WHERE email=?', (admin_email,)).fetchone()
    if not existing:
        conn.execute('INSERT INTO users(name,email,password_hash,is_admin) VALUES(?,?,?,1)', ('AURA Admin', admin_email, generate_password_hash(admin_password)))
    conn.commit(); conn.close()

@app.context_processor
def inject_globals():
    user = None
    if session.get('user_id'):
        user = db().execute('SELECT id,name,email,is_admin FROM users WHERE id=?', (session['user_id'],)).fetchone()
    cart = session.get('cart', {})
    return {'current_user': user, 'cart_count': sum(int(v.get('qty',1)) for v in cart.values()), 'year': 2026}

def login_required(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        if not session.get('user_id'):
            flash('Please sign in to continue.', 'info'); return redirect(url_for('login', next=request.path))
        return fn(*a, **kw)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        u = db().execute('SELECT is_admin FROM users WHERE id=?', (session.get('user_id', -1),)).fetchone()
        if not u or not u['is_admin']: abort(403)
        return fn(*a, **kw)
    return wrapped

def csrf_token():
    if '_csrf' not in session: session['_csrf'] = secrets.token_urlsafe(24)
    return session['_csrf']
app.jinja_env.globals['csrf_token'] = csrf_token
@app.before_request
def csrf_protect():
    if request.method == 'POST':
        token = request.form.get('_csrf') or request.headers.get('X-CSRF-Token')
        if not token or not secrets.compare_digest(token, session.get('_csrf', '')):
            abort(400, 'Invalid or expired form token. Refresh and try again.')

def get_cart_rows():
    cart = session.get('cart', {})
    ids = []
    for key in cart:
        try: ids.append(int(str(key).split(':',1)[0]))
        except ValueError: pass
    ids = sorted(set(ids))
    if not ids: return [], 0
    placeholders = ','.join('?' for _ in ids)
    rows = db().execute(f'SELECT * FROM products WHERE active=1 AND id IN ({placeholders})', ids).fetchall()
    products = {str(p['id']): p for p in rows}
    items=[]; subtotal=0
    for key, val in cart.items():
        product_id=str(key).split(':',1)[0]
        p=products.get(product_id)
        try: qty=max(1,min(10,int(val.get('qty',1))))
        except (ValueError,AttributeError): qty=1
        size=val.get('size','One Size') if isinstance(val,dict) else 'One Size'
        if p:
            line=p['price']*qty; subtotal+=line; items.append({'key':key,'product':p,'qty':qty,'size':size,'line':line})
    return items, subtotal

@app.route('/')
def home():
    category=request.args.get('category','All'); q=request.args.get('q','').strip(); sort=request.args.get('sort','featured')
    sql='SELECT * FROM products WHERE active=1'; params=[]
    if category!='All': sql+=' AND category=?'; params.append(category)
    if q: sql+=' AND (name LIKE ? OR brand LIKE ? OR description LIKE ?)'; params += [f'%{q}%']*3
    sql += {'price-low':' ORDER BY price ASC','price-high':' ORDER BY price DESC','newest':' ORDER BY id DESC'}.get(sort,' ORDER BY id ASC')
    products=db().execute(sql,params).fetchall()
    cats=[r['category'] for r in db().execute('SELECT DISTINCT category FROM products WHERE active=1 ORDER BY category')]
    return render_template('home.html', products=products, categories=cats, category=category, q=q, sort=sort)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product=db().execute('SELECT * FROM products WHERE id=? AND active=1',(product_id,)).fetchone()
    if not product: abort(404)
    return render_template('product.html', product=product)

@app.route('/cart')
def cart_page():
    items, subtotal=get_cart_rows(); shipping=0 if subtotal>=1999 or subtotal==0 else 99
    coupon=session.get('coupon',''); discount=int(subtotal*({'AURA10':.10,'STYLE15':.15}.get(coupon,0))) if subtotal>=999 else 0
    return render_template('cart.html', items=items, subtotal=subtotal, shipping=shipping, total=subtotal+shipping, discount=discount, coupon=coupon)

@app.post('/cart/add/<int:product_id>')
def cart_add(product_id):
    p=db().execute('SELECT * FROM products WHERE id=? AND active=1',(product_id,)).fetchone()
    if not p: abort(404)
    size=request.form.get('size','One Size').strip()
    sizes=[s.strip() for s in p['sizes'].split(',')]
    if size not in sizes: flash('Please choose a valid size.', 'error'); return redirect(url_for('product_detail',product_id=product_id))
    key=f'{product_id}:{size}'
    cart=session.get('cart',{}); current=cart.get(key, {'qty':0,'size':size})
    try: add_qty=max(1,min(10,int(request.form.get('qty',1))))
    except ValueError: add_qty=1
    current['qty']=min(10,int(current.get('qty',0))+add_qty)
    cart[key]=current; session['cart']=cart; session.modified=True
    flash('Added to your bag.', 'success'); return redirect(request.referrer or url_for('home'))

@app.post('/cart/update')
def cart_update():
    cart=session.get('cart',{}); key=request.form.get('key',''); action=request.form.get('action')
    if key in cart:
        if action=='remove': cart.pop(key,None)
        else:
            try: qty=max(1,min(10,int(request.form.get('qty',1))))
            except ValueError: qty=1
            cart[key]['qty']=qty
    session['cart']=cart; return redirect(url_for('cart_page'))

@app.post('/coupon/apply')
def apply_coupon():
    code=request.form.get('coupon','').strip().upper()
    if request.form.get('clear'):
        session.pop('coupon',None); flash('Coupon removed.','info')
    elif code in ('AURA10','STYLE15'):
        _, subtotal=get_cart_rows()
        if subtotal < 999: flash('Coupon requires a cart subtotal of ₹999 or more.','error')
        else: session['coupon']=code; flash(f'{code} applied successfully.','success')
    else: flash('Invalid coupon. Try AURA10 or STYLE15.','error')
    return redirect(url_for('cart_page'))

@app.route('/wishlist')
@login_required
def wishlist_page():
    rows=db().execute('SELECT p.* FROM wishlist w JOIN products p ON p.id=w.product_id WHERE w.user_id=? AND p.active=1 ORDER BY p.name',(session['user_id'],)).fetchall()
    return render_template('wishlist.html', products=rows)

@app.post('/wishlist/toggle/<int:product_id>')
@login_required
def wishlist_toggle(product_id):
    if not db().execute('SELECT id FROM products WHERE id=? AND active=1',(product_id,)).fetchone(): abort(404)
    conn=db(); exists=conn.execute('SELECT 1 FROM wishlist WHERE user_id=? AND product_id=?',(session['user_id'],product_id)).fetchone()
    if exists: conn.execute('DELETE FROM wishlist WHERE user_id=? AND product_id=?',(session['user_id'],product_id)); flash('Removed from wishlist.','info')
    else: conn.execute('INSERT OR IGNORE INTO wishlist(user_id,product_id) VALUES(?,?)',(session['user_id'],product_id)); flash('Saved to wishlist.','success')
    conn.commit(); return redirect(request.referrer or url_for('home'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        if len(name)<2 or '@' not in email or len(password)<8:
            flash('Enter a valid name/email and a password with at least 8 characters.','error')
        else:
            try:
                cur=db().execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',(name,email,generate_password_hash(password))); db().commit()
                session.clear(); session['user_id']=cur.lastrowid; flash('Welcome to AURA.','success'); return redirect(url_for('home'))
            except sqlite3.IntegrityError: flash('An account with that email already exists.','error')
    return render_template('auth.html', mode='register')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        u=db().execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if u and check_password_hash(u['password_hash'],password):
            session.clear(); session['user_id']=u['id']; flash('You are signed in.','success')
            dest=request.args.get('next',''); return redirect(dest if dest.startswith('/') and not dest.startswith('//') else url_for('home'))
        flash('Email or password is incorrect.','error')
    return render_template('auth.html', mode='login')

@app.post('/logout')
def logout(): session.clear(); flash('You have signed out.','info'); return redirect(url_for('home'))

@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    items, subtotal=get_cart_rows(); shipping=0 if subtotal>=1999 or subtotal==0 else 99
    coupon=session.get('coupon',''); discount=int(subtotal*({'AURA10':.10,'STYLE15':.15}.get(coupon,0))) if subtotal>=999 else 0
    if not items: flash('Your bag is empty.','info'); return redirect(url_for('home'))
    user=db().execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone()
    if request.method=='POST':
        name=request.form.get('name','').strip(); phone=''.join(c for c in request.form.get('phone','') if c.isdigit()); address=request.form.get('address','').strip(); city=request.form.get('city','').strip(); pin=request.form.get('pin','').strip()
        if len(name)<2 or len(phone) not in (10,11,12,13,14,15) or len(address)<5 or len(city)<2 or len(pin)!=6 or not pin.isdigit():
            flash('Please check your delivery details.','error')
        else:
            conn=db(); order_no='AU'+secrets.token_hex(4).upper()
            cur=conn.execute('INSERT INTO orders(order_no,user_id,customer_name,phone,address,city,pin,payment_method,status,subtotal,shipping,total) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(order_no,session['user_id'],name,phone,address,city,pin,'COD','Placed',subtotal-discount,shipping,subtotal+shipping-discount))
            oid=cur.lastrowid
            for item in items:
                p=item['product']; conn.execute('INSERT INTO order_items(order_id,product_id,product_name,size,qty,unit_price) VALUES(?,?,?,?,?,?)',(oid,p['id'],p['name'],item['size'],item['qty'],p['price']))
            conn.commit(); session['cart']={}; session.pop('coupon',None); session['just_ordered']=True; flash(f'Order {order_no} placed with Cash on Delivery. This is a local demo order; no courier is connected.','success'); return redirect(url_for('order_detail',order_id=oid))
    return render_template('checkout.html', items=items, subtotal=subtotal, shipping=shipping, total=subtotal+shipping-discount, discount=discount, coupon=coupon, user=user)

@app.route('/account/orders')
@login_required
def orders_page():
    rows=db().execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall()
    return render_template('orders.html', orders=rows)

@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order=db().execute('SELECT * FROM orders WHERE id=? AND user_id=?',(order_id,session['user_id'])).fetchone()
    if not order: abort(404)
    items=db().execute('SELECT * FROM order_items WHERE order_id=?',(order_id,)).fetchall()
    just_ordered=session.pop('just_ordered',False)
    return render_template('order_detail.html', order=order, items=items, just_ordered=just_ordered)

@app.route('/admin')
@login_required
@admin_required
def admin():
    conn=db(); products=conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); orders=conn.execute('SELECT o.*,u.email FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC LIMIT 100').fetchall()
    stats={'products':conn.execute('SELECT COUNT(*) FROM products WHERE active=1').fetchone()[0], 'orders':conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0], 'users':conn.execute('SELECT COUNT(*) FROM users WHERE is_admin=0').fetchone()[0], 'sales':conn.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status!='Cancelled'").fetchone()[0]}
    return render_template('admin.html', products=products, orders=orders, stats=stats)

@app.route('/admin/product', methods=['POST'])
@login_required
@admin_required
def admin_product_add():
    f=request.form
    try:
        price=int(f.get('price','0')); old=int(f.get('old_price','0'))
        if price<1 or old<price: raise ValueError
        db().execute('INSERT INTO products(name,brand,category,price,old_price,sizes,color,image,description) VALUES(?,?,?,?,?,?,?,?,?)',(f['name'].strip(),f['brand'].strip(),f['category'],price,old,f.get('sizes','One Size').strip(),f.get('color','').strip(),f.get('image','').strip(),f.get('description','').strip())); db().commit(); flash('Product added.','success')
    except (ValueError, KeyError): flash('Check product fields. Price must be positive and MRP should be at least the selling price.','error')
    return redirect(url_for('admin'))

@app.post('/admin/product/<int:product_id>/toggle')
@login_required
@admin_required
def admin_product_toggle(product_id):
    db().execute('UPDATE products SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?',(product_id,)); db().commit(); flash('Product visibility updated.','success'); return redirect(url_for('admin'))

@app.post('/admin/order/<int:order_id>/status')
@login_required
@admin_required
def admin_order_status(order_id):
    status=request.form.get('status')
    if status not in ['Placed','Confirmed','Packed','Shipped','Delivered','Cancelled']: abort(400)
    db().execute('UPDATE orders SET status=? WHERE id=?',(status,order_id)); db().commit(); flash('Order status updated.','success'); return redirect(url_for('admin')+'#orders')

@app.errorhandler(403)
def forbidden(e): return render_template('message.html', title='Access denied', message='This page is only available to an AURA administrator.'),403
@app.errorhandler(404)
def not_found(e): return render_template('message.html', title='Page not found', message='We could not find that page or product.'),404

init_db()
if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT','5000')), debug=False)
