from . import db

class Books(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(10),  nullable=False)
    title = db.Column(db.String(50), nullable=False)
    img_name = db.Column(db.String(20), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(5), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Orders(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(10),  nullable=False)
    cust_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10),nullable=False)
    address = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    resell_status = db.Column(db.String(20), nullable=True)

class Orderstemp(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(10),  nullable=False)
    cust_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)


class Users(db.Model):
    cust_id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(50), nullable=False)