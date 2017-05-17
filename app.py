from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from yahoo_finance import Share
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'albythoconnect'
app.config['MONGO_URI'] = 'mongodb://albytho:Brownknight97@ds143151.mlab.com:43151/albythoconnect'
mongo = PyMongo(app)


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
    user = mongo.db.users
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        user.insert({'name' : name, 'username' : username, 'email' : email, 'password' : password, 'buying_power' : 10000})
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    user = mongo.db.users
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        query = user.find_one({'username': username})

        if query is not None:
            password = query['password']
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid login"
                return render_template('login.html',error=error)
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
    user = mongo.db.users
    buying_power = user.find_one({'name': 'John'})['buying_power']
    return render_template('dashboard.html',money=buying_power)

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
