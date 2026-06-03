from os import name
import os
import uuid
from flask import Flask, render_template, request
from database import Menu, Session
from flask import session
app = Flask(__name__)
app.secret_key="3423355uiotyye4354gffdt4t4fdhty53"

@app.route("/")
def index():
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

@app.route("/order/", methods = ["POST"])
def order():
    id = request.form.get('id')
    with Session() as cursor:
        position = cursor.query(Menu).filter_by(id=id).first()
    orders=session.get("my_orders",None)
    if orders==None:
        orders=[]
        print("create order")
    orders.append(position.id)
    session["my_orders"]=orders
    return f"{position.name} Додано до замовлення <a href='/'>головна</a> <a href='/checkout_order/'>оформити</a>"

@app.route("/check_order/")
def check_orders():
    return session['my_orders']

@app.route("/checkout_order/")
def checkout_order():
    orders=session.get("my_orders",None)
    with Session() as cursor:
        positions =  [post for post in cursor.query(Menu).filter_by().all() if post.id in orders]
    return render_template("order.html",positions=positions)
    
if __name__ == "__main__":
    app.run()