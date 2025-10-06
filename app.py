from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# SQLite Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- MODELS (Database Tables) ---------- #
class Product(db.Model):
    product_id = db.Column(db.String(50), primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)

class Location(db.Model):
    location_id = db.Column(db.String(50), primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)

class ProductMovement(db.Model):
    movement_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_location = db.Column(db.String(50), db.ForeignKey('location.location_id'))
    to_location = db.Column(db.String(50), db.ForeignKey('location.location_id'))
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'))
    qty = db.Column(db.Integer, nullable=False)

# ---------- ROUTES ---------- #
@app.route('/')
def home():
    return render_template('base.html')

# ---- PRODUCTS ---- #
@app.route('/products')
def view_products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    pid = request.form['product_id']
    name = request.form['product_name']
    db.session.add(Product(product_id=pid, product_name=name))
    db.session.commit()
    return redirect(url_for('view_products'))

# ---- LOCATIONS ---- #
@app.route('/locations')
def view_locations():
    locations = Location.query.all()
    return render_template('locations.html', locations=locations)

@app.route('/add_location', methods=['POST'])
def add_location():
    lid = request.form['location_id']
    name = request.form['location_name']
    db.session.add(Location(location_id=lid, location_name=name))
    db.session.commit()
    return redirect(url_for('view_locations'))

# ---- MOVEMENTS ---- #
@app.route('/movements')
def view_movements():
    movements = ProductMovement.query.all()
    products = Product.query.all()
    locations = Location.query.all()
    return render_template('movements.html', movements=movements, products=products, locations=locations)

@app.route('/add_movement', methods=['POST'])
def add_movement():
    product_id = request.form['product_id']
    from_location = request.form.get('from_location') or None
    to_location = request.form.get('to_location') or None
    qty = int(request.form['qty'])
    move = ProductMovement(product_id=product_id, from_location=from_location, to_location=to_location, qty=qty)
    db.session.add(move)
    db.session.commit()
    return redirect(url_for('view_movements'))

# ---- REPORT ---- #
@app.route('/report')
def report():
    products = Product.query.all()
    locations = Location.query.all()
    report_data = []

    for p in products:
        for l in locations:
            in_qty = db.session.query(db.func.sum(ProductMovement.qty)).filter(
                ProductMovement.product_id == p.product_id,
                ProductMovement.to_location == l.location_id
            ).scalar() or 0

            out_qty = db.session.query(db.func.sum(ProductMovement.qty)).filter(
                ProductMovement.product_id == p.product_id,
                ProductMovement.from_location == l.location_id
            ).scalar() or 0

            balance = in_qty - out_qty
            if balance != 0:
                report_data.append({
                    'product': p.product_name,
                    'location': l.location_name,
                    'qty': balance
                })
    return render_template('report.html', report=report_data)

# ---------- MAIN ---------- #
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
