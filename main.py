from flask import Flask, render_template
from database import Menu, Session


app = Flask(__name__)


@app.route("/")
def index():
    with Session() as cursor:
        positions = cursor.query(Menu).all()
    return render_template("home.html", positions=positions)


if __name__ == "__main__":
    app.run()
