from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from models import *
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from yahoo_finance import Share

app = Flask(__name__)


@app.before_request
def before_request():
    initialize_db()

@app.teardown_request
def teardown_request(exception):
    db.close()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search', methods=['GET','POST'])
def search_post():
    if request.method == 'POST':
        text = request.form['stock']
        stock = text.upper()
        stock_price = Share(str(stock)).get_price()
        return render_template('search.html',stock_price=stock_price)
    else:
        return render_template('search.html')

@app.route('/buy', methods=['GET','POST'])
def buy():
    if request.method == 'POST':
        text = request.form['stock']
        stock = text.upper()
        quantity = float(request.form['quantity'])

        total_cost = float(Share(str(stock)).get_price())*quantity
        portfolio = User.get(User.username == session['username']).portfolio
        buying_power = User.get(User.username == session['username']).money

        if buying_power >= total_cost:
            if portfolio.get(stock) is None:
                portfolio[stock] = quantity

                User.get(User.username == session['username']).money = buying_power - total_cost
                User.get(User.username == session['username']).save()
            return redirect(url_for('dashboard'))

    return render_template('buy.html')

@app.route('/sell')
def sell():
    return render_template('sell.html')

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        User.create(name=name, username=username, email=email, password=password)
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        query = User.select().where(User.username == username)

        if query.exists():
            password = User.get(User.username == username).password
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid login"
                return render_template('login.html',error=error)

            db.close()
        else:
            error = "Username not found"
            return render_template('login.html',error=error)

    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    money = User.get(User.username == session['username']).money
    return render_template('dashboard.html',money=money)

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
