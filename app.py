from flask import Flask, request, render_template,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user,UserMixin,current_user,login_required 
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://u4tzta1s5zsm2y0zttlz:!!!addPASSWORD!!!@b0hooldw2cdg4khzlgeq-postgresql.services.clever-cloud.com:50013/b0hooldw2cdg4khzlgeq'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.secret_key='topmost_secret_key'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models.usersDB import Users

# Make Users model compatible with Flask-Login
class UserLogin(Users, UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    show_modal = False
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password_hash']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        existing_user = Users.query.filter((Users.username == username) | (Users.email == email)).first()
        if existing_user:
            error = 'Username or email already exists. Please choose another.'
            show_modal = True
        else:
            new_user = Users(username=username, email=email, password_hash=hashed_password, created_at=db.func.current_timestamp())
            db.session.add(new_user)
            db.session.commit()
            return redirect('/')
    return render_template('register.html', error=error, show_modal=show_modal)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    show_modal = False
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password_hash']
        user = Users.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index' , username=username))
        else:
            error = 'Invalid username or password.'
            show_modal = True
    return render_template('login.html', error=error, show_modal=show_modal)

@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect('/')

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    return render_template('admin.html')


if __name__ == '__main__':
    app.run()