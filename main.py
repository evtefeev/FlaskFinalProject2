from os import name
import os
import uuid

from flask import Flask, render_template, request
from database import Menu, Session


app = Flask(__name__)


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


if __name__ == "__main__":
    app.run()
