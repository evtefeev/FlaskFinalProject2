from datetime import datetime
from os import name
import os
import secrets
import uuid
from flask import Flask, flash, redirect, render_template, request, url_for
from database import Menu, Orders, Session, Users
from flask import session
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

app = Flask(__name__)
app.secret_key = "3423355uiotyye4354gffdt4t4fdhty53"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    with Session() as session:
        return session.query(Users).filter_by(id=user_id).first()


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
                    "register.html", csrf_token=session["csrf_token"]
                )

            new_user = Users(nickname=nickname, email=email)
            new_user.set_password(password)
            cursor.add(new_user)
            cursor.commit()
            cursor.refresh(new_user)
            login_user(new_user)
            return redirect(url_for("index"))
    return render_template("register.html", csrf_token=session["csrf_token"])


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

    return render_template("login.html", csrf_token=session["csrf_token"])


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    with Session() as cursor:
        positions = cursor.query(Menu).all()
    return render_template("home.html", positions=positions)


@app.route("/add_position", methods=["GET", "POST"])
def add_position():
    if request.method == "POST":
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

    return render_template("add_position.html")


@app.route("/menu/<id>")
def menu(id):
    with Session() as cursor:
        position = cursor.query(Menu).filter_by(id=id).first()
    return render_template("position.html", position=position)


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
    with Session() as cursor:
        positions = [
            post for post in cursor.query(Menu).filter_by().all() if post.id in orders
        ]

    if request.method == "POST":
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

    return render_template("order.html", positions=positions)


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
                        {"name": user_order.name, "image": user_order.image, "username": user.nickname}
                    )
                    print(user_order.name)
                    print(user_order.image)


    return render_template("orders.html", orders=orders)


if __name__ == "__main__":
    app.run()
