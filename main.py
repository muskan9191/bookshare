from flask import Flask, render_template, request, session, url_for, flash,g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random
from werkzeug.utils import secure_filename, redirect
from PayTm import Checksum
# from flask_wtf import CSRFProtect
import json
app = Flask(__name__)
db = SQLAlchemy(app)

with open('config.json',"r") as C:
    params = json.load(C)["params"]

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/bookshare"
app.config['UPLOAD_FOLDER']=params['upload_Location']
app.secret_key = params['secret_key']
#Provided by Paytm
MERCHANT_KEY = params['merchant_key']

# csrf = CSRFProtect(app)
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


@app.before_request
def before_request():
    g.user = None
    g.admin = None
    if 'email' in session:
        user = Users.query.filter_by(email=session['email']).first()
        g.user = user
    if 'admin' in session:
        g.admin = "admin"

#signup form
@app.route("/signup",methods=["GET", "POST"])
def signup():
    session.pop('email', None)
    if request.method == "POST":
        session.pop('email', None)
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        address = request.form.get('address')
        password = request.form.get('password')
        phone = request.form.get('phn')
        confirm = request.form.get('cfpwd')
        if password == confirm:
            deca = Users(firstname=fname,lastname=lname, email=email,password=password,phone=phone,address=address)
            db.session.add(deca)
            db.session.commit()
            flash("Registered Successfully", "success")
            return redirect(url_for('login'))

        else:
            flash("Password does not match", "danger")
            return redirect(url_for('signup'))
    return render_template("signup.html")

@app.route("/", methods=["GET","POST"])
def login():
    session.pop('email', None)
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        cheka = Users.query.filter_by(email=email,password=password).first()
        if cheka:
            session['cust_id'] = cheka.cust_id
            session['email'] = email
            return redirect(url_for('home'))
        else:
            flash("The Email and Password does not match our records", "danger")
            return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/home")
def home():
    if not g.user:
        return redirect(url_for('login'))
    # deca = Books.query.filter_by(tag="bestseller").all()
    # return render_template("homepage.html", books=deca)
    return render_template("homepage.html")

@app.route("/newbooks")
def newbooks():
    if not g.user:
        return redirect(url_for('login'))
    deca = Books.query.filter_by(status="new").all()
    return render_template("newbooks.html", books=deca,status="new")

@app.route("/oldbooks")
def oldbooks():
    if not g.user:
        return redirect(url_for('login'))
    deca = Books.query.filter_by(status="old").all()
    return render_template("oldbooks.html", books=deca,status="old")

@app.route("/buy/<string:sno>", methods=['GET','POST'])
def buy(sno):
    if not g.user:
        return redirect(url_for('login'))
    book = Books.query.filter_by(srno=sno).first()
    return render_template('buy.html', book=book)

@app.route("/address/<string:sno>", methods=['GET','POST'])
def address(sno):
    if not g.user:
        return redirect(url_for('login'))
    if request.method == "POST":
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        option = request.form['options']
        cust_id = request.form.get('cust_id')
        book_id = request.form.get('book_id')
        status = request.form.get('status')
        bookid = book_id.split('-')
        book = Books.query.filter_by(srno=sno).first()
        address = address + " " + pincode
        amount = float(price) * float(quantity)
        if status == "new":
            order_id = "ORD-11" + "0" + cust_id + bookid[1] + str(random.randint(1000, 9999))
            session['order_id'] = order_id
        else:
            order_id = "ORD-00" + "0" + cust_id + bookid[1] + str(random.randint(1000, 9999))
            session['order_id'] = order_id
        if option == "COD":
            date = datetime.now()
            peca = Orders(order_id = order_id, book_id = book_id, cust_id = cust_id, quantity = quantity, amount = amount,date = date,address = address ,resell_status="new",
                          payment_method = "Cash on Delivery")
            db.session.add(peca)
            db.session.commit()
            deca = Books.query.filter_by(book_id = book_id).first()
            deca.quantity = int(deca.quantity) - 1
            db.session.commit()
            return redirect(url_for('order',sno=book.srno))
        else:
            date = datetime.now()
            peca = Orderstemp(order_id=order_id, book_id=book_id, cust_id=cust_id, quantity=quantity, amount=amount,date = date,
                              address=address, payment_method="Online Payment")
            db.session.add(peca)
            db.session.commit()
            # This dic wil be sent to paytm
            param_dict = {
                'MID': 'Replace with your MID',
                'ORDER_ID': order_id,
                'TXN_AMOUNT': str(amount),
                'CUST_ID': 'Customer',
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'DEFAULT',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL': 'http://127.0.0.1:5000/handlerequest',
            }
            # checksumhash is generated
            param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
            #AN intermdiate page will be used to give a post request to Paytm
            return render_template("paytm.html", MID='ViuoXq02464757024003', ORDER_ID=order_id, amount=str(amount),
                                   cust_id='Customer', industry_name="Retail", Channel_id="WEB", Website="DEFAULT",
                                   callback="http://127.0.0.1:5000/handlerequest",
                                   CHECKSUMHASH=param_dict['CHECKSUMHASH'])
    book = Books.query.filter_by(srno=sno).first()
    return render_template("address.html" ,book = book)

@app.route("/order/<string:sno>")
def order(sno):
    if not g.user:
        return redirect(url_for('login'))
    book = Books.query.filter_by(srno=sno).first()
    order_id = session['order_id']
    order = Orders.query.filter_by(order_id = order_id).first()
    return render_template('order.html', book=book,order=order)

@app.route("/handlerequest", methods=["GET", "POST"])
def handlerequest():
    if request.method == "POST":
        b = request.get_data().decode("utf-8")
        b = b.replace('&', ',')
        b = b.replace('=', ':')
        print(b)
        form = {}
        list = b.split(',')
        for item in list:
            key = item.split(':')[0]
            value = item.split(':')[1]
            form[key] = value
        responsedict = {}
        for i in form.keys():
            responsedict[i] = form[i]
            if i == "CHECKSUMHASH":
                checksum = form[i]
        if responsedict["RESPCODE"] == "01":
            order_id = responsedict["ORDERID"]
            ordertemp = Orderstemp.query.filter_by(order_id=order_id).first()
            book_id = ordertemp.book_id
            cust_id = ordertemp.cust_id
            quantity = ordertemp.quantity
            amount = ordertemp.amount
            address = ordertemp.address
            payment_method = ordertemp.payment_method
            date = datetime.now()
            peca = Orders(order_id=order_id, book_id=book_id, cust_id=cust_id, quantity=quantity, amount=amount,date = date,
                          address=address, payment_method = payment_method)
            db.session.add(peca)
            db.session.commit()
            deca = Books.query.filter_by(book_id=book_id).first()
            deca.quantity = int(deca.quantity) - 1
            db.session.commit()
            return redirect(url_for('order', sno=deca.srno))
        return "Thank you"
# BANKTXNID:,CHECKSUMHASH:Z%2Bu2wlpLPsp4U7CesNUdqWvvCJGDx%2BfWYJyh2xaI7NeHcw9Y3grdWiS4N3Ket46znqje2yaoMpS%2BopNSUy9i0LhsnzvDsbPslhkf8AKwBn0%3D,
# CURRENCY:INR,MID:ViuoXq02464757024003,ORDERID:ORD-1101553215637,RESPCODE:501,RESPMSG:System+Error,STATUS:TXN_FAILURE,TXNAMOUNT:1.00

@app.route("/myorders", methods=['GET','POST'])
def myorders():
    if not g.user:
        return redirect(url_for('login'))
    # if request.method == "POST":
    #     order_id = request.form.get('order_id')
    #     book_id = request.form.get('book_id')
    #     order = Orders.query.filter_by(order_id = order_id).first()
    #     book = Books.query.filter_by(book_id = book_id).first()
    #     redirect(url_for('resell',order = order,book = book))
    orders = Orders.query.filter_by(cust_id = session['cust_id']).all()
    books = []
    for order in orders:
        book_id = order.book_id
        books.append(Books.query.filter_by(book_id=book_id).first())
    return render_template('myorders.html',packed = zip(books,orders))

@app.route("/resell/<string:order_id>/<string:book_id>")
def resell(order_id,book_id):
    if not g.user:
        return redirect(url_for('login'))
    book = Books.query.filter_by(book_id=book_id).first()
    order = Orders.query.filter_by(order_id=order_id).first()
    return render_template("resell.html",book=book,order=order)

@app.route("/bookPay")
def bookpay():
    if not g.user:
        return redirect(url_for('login'))
    return render_template("bookpay.html")


@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        if email == "admin" and password == "admin@123":
            session['admin'] = email
            return redirect(url_for('dashboard'))
        else:
            flash("Wrong Credentials", "danger")
            return redirect(url_for('admin'))
    return render_template("admin.html")

@app.route("/adminlogout", methods=["GET","POST"])
def adminlogout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not g.admin:
        return redirect(url_for('admin'))
    if request.method == "POST":
        title = request.form.get('title')
        author = request.form.get('author')
        price = request.form.get('price')
        book_id = request.form.get('book_id')
        nob = request.form.get('nob')
        f = request.files['file1']
        book = "BS1-" + book_id
        print(book)
        deca = Books.query.filter_by(book_id = book,status = "new").first()
        if deca is None:
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            peca = Books(book_id = book,title=title,author=author,quantity=nob,img_name=f.filename,price=price,status="new")
            db.session.add(peca)
            db.session.commit()
            flash("Uploaded Successfully", "Success")
            return redirect(url_for('dashboard'))
        else:
            deca.quantity = int(deca.quantity) + int(nob)
            db.session.commit()
            print(deca.quantity)
            print(nob)
            flash("Uploaded Successfully(already present quantity incremented)", "Success")
            return redirect(url_for('dashboard'))
    return render_template("dashboard.html")

if __name__=="__main__":
    app.run(debug=True)