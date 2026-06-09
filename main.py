from datetime import datetime
from os import name
import os
import secrets
import uuid
from flask import Flask, flash, g, redirect, render_template, request, url_for
from database import Menu, Orders, Session, Users
from flask import session
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
app.config["MAX_FORM_MEMORY_SIZE"] = 1024 * 1024  # 1MB
app.config["MAX_FORM_PARTS"] = 500  # Ліміт 500 полів


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    with Session() as session:
        return session.query(Users).filter_by(id=user_id).first()


@app.before_request
def generate_nonce():
    g.csp_nonce = secrets.token_urlsafe(16)

@app.after_request
def apply_csp(response):
    nonce = getattr(g, "csp_nonce", "")

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self' 'nonce-{nonce}'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "object-src 'none';"
    )

    return response


@app.context_processor
def context():
    return {
        "csp_nonce": getattr(g, "csp_nonce", ""),
        "user": current_user,
        "csrf_token": session["csrf_token"]
    }


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form.get("csrf_token") != session["csrf_token"]:
            return "Запит заблоковано!", 403
        nickname = request.form["nickname"]
        email = request.form["email"]
        password = request.form["password"]

        with Session() as cursor:
            if (
                cursor.query(Users).filter_by(email=email).first()
                or cursor.query(Users).filter_by(nickname=nickname).first()
            ):
                flash("Користувач з таким email або нікнеймом вже існує!", "danger")
                return render_template(
                    "register.html"
                )

            new_user = Users(nickname=nickname, email=email)
            new_user.set_password(password)
            cursor.add(new_user)
            cursor.commit()
            cursor.refresh(new_user)
            login_user(new_user)
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("csrf_token") != session["csrf_token"]:
            return "Запит заблоковано!", 403

        nickname = request.form["nickname"]
        password = request.form["password"]

        with Session() as cursor:
            user = cursor.query(Users).filter_by(nickname=nickname).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("index"))

            flash("Неправильний nickname або пароль!", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    with Session() as cursor:
        positions = cursor.query(Menu).filter_by(show=True).all()
    return render_template(
        "home.html",
        positions=positions,
        user=current_user,
        csp_nonce=g.csp_nonce,
    )


@app.route("/add_position", methods=["GET", "POST"])
def add_position():
    if current_user.nickname != "admin":
        return "Запит заблоковано!", 403
    if request.method == "POST":
        if request.form.get("csrf_token") != session["csrf_token"]:
            return "Запит заблоковано!", 403
        name = request.form.get("name")
        desc = request.form.get("desc")
        time = int(request.form.get("time"))
        cost = int(request.form.get("cost"))
        image = request.files.get("image")

        # print(name, desc, time, cost, image)

        if not image or not image.filename:
            return "Файл не вибрано або завантаження не вдалося"

        unique_filename = f"{uuid.uuid4()}_{image.filename}"
        output_path = os.path.join("static/menu", unique_filename)

        with open(output_path, "wb") as f:
            f.write(image.read())

        item = Menu(
            name=name,
            image=output_path,
            description=desc,
            time=time,
            cost=cost,
        )
        with Session() as cursor:
            cursor.add(item)
            cursor.commit()

        return "Позиція успішно додана!"

    return render_template(
        "add_position.html",
        user=current_user.nickname,
        csrf_token=session["csrf_token"],
    )


@app.route("/menu/<id>")
def menu(id):
    with Session() as cursor:
        position = cursor.query(Menu).filter_by(id=id).first()
    return render_template(
        "position.html", position=position
    )


@app.route("/order/", methods=["POST"])
def order():
    id = request.form.get("id")
    with Session() as cursor:
        position = cursor.query(Menu).filter_by(id=id).first()
    orders = session.get("my_orders", None)
    if orders == None:
        orders = []
        print("create order")
    orders.append(position.id)
    session["my_orders"] = orders
    return f"{position.name} Додано до замовлення <a href='/'>головна</a> <a href='/checkout_order/'>оформити</a>"


@app.route("/check_order/")
def check_orders():
    return session["my_orders"]


@app.route("/checkout_order/", methods=["GET", "POST"])
def checkout_order():
    orders = session.get("my_orders", None)
    positions = []
    if orders:
        with Session() as cursor:
            positions = [
                post
                for post in cursor.query(Menu).filter_by().all()
                if post.id in orders
            ]

    if request.method == "POST":
        if request.form.get("csrf_token") != session["csrf_token"]:
            return "Запит заблоковано!", 403

        try:
            location = request.form.get("location")
            item = Orders(
                location=location,
                user_id=current_user.id,
                order_list=" ".join(map(str, orders)),
                order_time=datetime.now(),
            )
        except AttributeError:
            return redirect(url_for("login"))
        with Session() as cursor:
            cursor.add(item)
            cursor.commit()
        session.pop("my_orders")
        return render_template("thank.html")

    return render_template(
        "order.html",
        positions=positions
    )


@app.route("/orders/")
@login_required
def orders():
    if current_user.nickname != "admin":
        return "Немає доступу"
    orders = []
    with Session() as cursor:
        users = cursor.query(Users).all()
        for user in users:
            user_orders = [
                order
                for order in cursor.query(Orders).filter_by().all()
                if order.user_id == user.id
            ]

            if user_orders:
                for order in user_orders:
                    print(order)
                    user_order = cursor.query(Menu).filter_by(id=order.id).first()
                    orders.append(
                        {
                            "name": user_order.name,
                            "image": user_order.image,
                            "username": user.nickname,
                        }
                    )
                    print(user_order.name)
                    print(user_order.image)

    return render_template("orders.html", orders=orders)


if __name__ == "__main__":
    app.run(debug=True)
