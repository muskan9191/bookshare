from flask import render_template, request, session, url_for, flash, g, Blueprint, current_app
from datetime import datetime
import os
import random
from werkzeug.utils import secure_filename, redirect
from .payment_gateway import Checksum
from .models import Users, Books, Orders, Orderstemp, db

main = Blueprint('main', __name__)

@main.before_request
def before_request():
    g.user = None
    g.admin = None
    if 'email' in session:
        user = Users.query.filter_by(email=session['email']).first()
        g.user = user
    if 'admin' in session:
        g.admin = "admin"

#signup form
@main.route("/signup",methods=["GET", "POST"])
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
            return redirect(url_for('main.login'))

        else:
            flash("Password does not match", "danger")
            return redirect(url_for('main.signup'))
    return render_template("signup.html")

@main.route("/", methods=["GET","POST"])
def login():
    session.pop('email', None)
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        cheka = Users.query.filter_by(email=email,password=password).first()
        if cheka:
            session['user_id'] = cheka.user_id
            session['email'] = email
            return redirect(url_for('main.home'))
        else:
            flash("The Email and Password does not match our records", "danger")
            return redirect(url_for('main.login'))
    return render_template("index.html")

@main.route("/home")
def home():
    if not g.user:
        return redirect(url_for('main.login'))
    # deca = Books.query.filter_by(tag="bestseller").all()
    # return render_template("homepage.html", books=deca)
    return render_template("homepage.html")

@main.route("/newbooks")
def newbooks():
    if not g.user:
        return redirect(url_for('main.login'))
    deca = Books.query.filter_by(status="new").all()
    return render_template("newbooks.html", books=deca,status="new")

@main.route("/oldbooks")
def oldbooks():
    if not g.user:
        return redirect(url_for('main.login'))
    deca = Books.query.filter_by(status="old").all()
    return render_template("oldbooks.html", books=deca,status="old")

@main.route("/buy/<string:sno>", methods=['GET','POST'])
def buy(sno):
    if not g.user:
        return redirect(url_for('main.login'))
    book = Books.query.filter_by(srno=sno).first()
    return render_template('buy.html', book=book)

@main.route("/address/<string:sno>", methods=['GET','POST'])
def address(sno):
    if not g.user:
        return redirect(url_for('main.login'))
    if request.method == "POST":
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        option = request.form['options']
        user_id = request.form.get('user_id')
        book_id = request.form.get('book_id')
        status = request.form.get('status')
        bookid = book_id.split('-')
        book = Books.query.filter_by(srno=sno).first()
        address = address + " " + pincode
        amount = float(price) * float(quantity)
        if status == "new":
            order_id = "ORD-11" + "0" + user_id + bookid[1] + str(random.randint(1000, 9999))
            session['order_id'] = order_id
        else:
            order_id = "ORD-00" + "0" + user_id + bookid[1] + str(random.randint(1000, 9999))
            session['order_id'] = order_id
        if option == "COD":
            date = datetime.now()
            peca = Orders(order_id = order_id, book_id = book_id, user_id = user_id, quantity = quantity, amount = amount,date = date,address = address ,resell_status="new",
                          payment_method = "Cash on Delivery")
            db.session.add(peca)
            db.session.commit()
            deca = Books.query.filter_by(book_id = book_id).first()
            deca.quantity = int(deca.quantity) - 1
            db.session.commit()
            return redirect(url_for('main.order',sno=book.srno))
        else:
            date = datetime.now()
            peca = Orderstemp(order_id=order_id, book_id=book_id, user_id=user_id, quantity=quantity, amount=amount,date = date,
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
            param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, current_app.config['MERCHANT_KEY'])
            #AN intermdiate page will be used to give a post request to Paytm
            return render_template("paytm.html", MID='ViuoXq02464757024003', ORDER_ID=order_id, amount=str(amount),
                                   cust_id='Customer', industry_name="Retail", Channel_id="WEB", Website="DEFAULT",
                                   callback="http://127.0.0.1:5000/handlerequest",
                                   CHECKSUMHASH=param_dict['CHECKSUMHASH'])
    book = Books.query.filter_by(srno=sno).first()
    return render_template("address.html" ,book = book)

@main.route("/order/<string:sno>")
def order(sno):
    if not g.user:
        return redirect(url_for('main.login'))
    book = Books.query.filter_by(srno=sno).first()
    order_id = session['order_id']
    order = Orders.query.filter_by(order_id = order_id).first()
    return render_template('order.html', book=book,order=order)

@main.route("/handlerequest", methods=["GET", "POST"])
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
            user_id = ordertemp.user_id
            quantity = ordertemp.quantity
            amount = ordertemp.amount
            address = ordertemp.address
            payment_method = ordertemp.payment_method
            date = datetime.now()
            peca = Orders(order_id=order_id, book_id=book_id, user_id=user_id, quantity=quantity, amount=amount,date = date,
                          address=address, payment_method = payment_method)
            db.session.add(peca)
            db.session.commit()
            deca = Books.query.filter_by(book_id=book_id).first()
            deca.quantity = int(deca.quantity) - 1
            db.session.commit()
            return redirect(url_for('main.order', sno=deca.srno))
        return "Thank you"
# BANKTXNID:,CHECKSUMHASH:Z%2Bu2wlpLPsp4U7CesNUdqWvvCJGDx%2BfWYJyh2xaI7NeHcw9Y3grdWiS4N3Ket46znqje2yaoMpS%2BopNSUy9i0LhsnzvDsbPslhkf8AKwBn0%3D,
# CURRENCY:INR,MID:ViuoXq02464757024003,ORDERID:ORD-1101553215637,RESPCODE:501,RESPMSG:System+Error,STATUS:TXN_FAILURE,TXNAMOUNT:1.00

@main.route("/myorders", methods=['GET','POST'])
def myorders():
    if not g.user:
        return redirect(url_for('main.login'))
    # if request.method == "POST":
    #     order_id = request.form.get('order_id')
    #     book_id = request.form.get('book_id')
    #     order = Orders.query.filter_by(order_id = order_id).first()
    #     book = Books.query.filter_by(book_id = book_id).first()
    #     redirect(url_for('main.resell',order = order,book = book))
    orders = Orders.query.filter_by(user_id = session['user_id']).all()
    books = []
    for order in orders:
        book_id = order.book_id
        books.append(Books.query.filter_by(book_id=book_id).first())
    return render_template('myorders.html',packed = zip(books,orders))

@main.route("/resell/<string:order_id>/<string:book_id>")
def resell(order_id,book_id):
    if not g.user:
        return redirect(url_for('main.login'))
    book = Books.query.filter_by(book_id=book_id).first()
    order = Orders.query.filter_by(order_id=order_id).first()
    return render_template("resell.html",book=book,order=order)

@main.route("/bookPay")
def bookpay():
    if not g.user:
        return redirect(url_for('main.login'))
    return render_template("bookpay.html")


@main.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        if email == "admin" and password == "admin@123":
            session['admin'] = email
            return redirect(url_for('main.dashboard'))
        else:
            flash("Wrong Credentials", "danger")
            return redirect(url_for('main.admin'))
    return render_template("admin.html")

@main.route("/adminlogout", methods=["GET","POST"])
def adminlogout():
    session.pop('admin', None)
    return redirect(url_for('main.admin'))

@main.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not g.admin:
        return redirect(url_for('main.admin'))
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
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            peca = Books(book_id = book,title=title,author=author,quantity=nob,img_name=f.filename,price=price,status="new")
            db.session.add(peca)
            db.session.commit()
            flash("Uploaded Successfully", "Success")
            return redirect(url_for('main.dashboard'))
        else:
            deca.quantity = int(deca.quantity) + int(nob)
            db.session.commit()
            print(deca.quantity)
            print(nob)
            flash("Uploaded Successfully(already present quantity incremented)", "Success")
            return redirect(url_for('main.dashboard'))
    return render_template("dashboard.html")