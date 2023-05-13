import sqlite3
import os
from flask import Flask, render_template, request, g, flash, abort, session, url_for, redirect, make_response
from flask_login import LoginManager, login_manager, login_user, login_required, logout_user, current_user
from FDataBase import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from UserLogin import UserLogin

DATABASE = '/tmp/database.db'
DEBUG = True
SECRET_KEY = 'kldjvfslfegghdfkjvghkitusre'
MAX_CONTENT_LENGTH = 1024 * 1024

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(DATABASE=os.path.join(app.root_path, 'database.db')))


login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"

def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()
        db.close()


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route('/')
@login_required
def index():
    return render_template("index.html")

@app.route('/handbook')
@login_required
def handbook():
    return render_template("handbook.html")

@app.route('/coloristics')
@login_required
def coloristics():
    return render_template("coloristics.html")

@app.route('/composition')
@login_required
def composition():
    return render_template("composition.html")

@app.route('/floriography')
@login_required
def floriography():
    return render_template("floriography.html")

@app.route('/materiology')
@login_required
def materiology():
    return render_template("materiology.html")


@app.route('/blossom')
@login_required
def blossom():
    return render_template("blossom.html")


@app.route("/add_post", methods=["POST", "GET"])
def addPost():
    db = get_db()
    dbase = FDataBase(db)

    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.addPost(request.form['name'], request.form['post'], request.form['url'])
            if not res:
                flash('Ошибка добавления статьи', category='error')
            else:
                flash('Статья добавлена успешно', category='success')
        else:
            flash('Ошибка добавления статьи', category='error')

    return render_template('add_post.html')


@app.route("/post/<alias>")
@login_required
def showPost(alias):
    db = get_db()
    dbase = FDataBase(db)
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', title=title, post=post)

@app.route("/all_posts")
def showAllPosts():
    db = get_db()
    dbase = FDataBase(db)
    return render_template('all_posts.html', posts=dbase.getPostsAnonce())


@app.route("/login", methods=["POST", "GET"])
def login():
    db = get_db()
    dbase = FDataBase(db)
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == "POST":
        user = dbase.getUserByEmail(request.form['email'])
        if user and check_password_hash(user['psw'], request.form['psw']):
            userlogin = UserLogin().create(user)
            rm = True if request.form.get('remainme') else False
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("index"))

        flash("Неверная пара логин/пароль", "error")

    return render_template("login.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    db = get_db()
    dbase = FDataBase(db)
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['email']) > 4 \
                and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2']:
            hash = generate_password_hash(request.form['psw'])
            res = dbase.addUser(request.form['name'], request.form['email'], hash)
            if res:
                flash("Вы успешно зарегистрированы", "success")
                return redirect(url_for('login'))
            else:
                flash("Ошибка при добавлении в БД", "error")
        else:
            flash("Неверно заполнены поля", "error")

    return render_template("register.html")


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    dbase = FDataBase(db)
    print("load_user")
    return UserLogin().fromDB(user_id, dbase)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    db = get_db()
    dbase = FDataBase(db)
    return render_template("profile.html", title="Профиль")


@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    db = get_db()
    dbase = FDataBase(db)
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                    return redirect(url_for('profile'))
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")

    return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run(port=8095, host='127.0.0.1', debug=True)