from flask import Flask, render_template, request, redirect, url_for , session
import random
import sqlite3
from werkzeug.security import generate_password_hash , check_password_hash


app = Flask(__name__)
app.secret_key = "slepenais"


def get_db():
    return sqlite3.connect("datubaze.db")

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    return render_template("register.html")


@app.route("/izvelne")
def izvelne():
    return render_template("izvelne.html")


@app.route("/pieteikumi")
def pieteikumi():
    return render_template("pieteikumi.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
	app.run(debug=True)