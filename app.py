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


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        epasts = request.form.get('epasts')
        parole = request.form.get('parole')

        conn = sqlite3.connect("datubaze.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE epasts = ?", (epasts,))
        lietotajs = cur.fetchone()
        conn.close()

        if lietotajs and check_password_hash(lietotajs['parole'], parole):
            session['id'] = lietotajs['id']
            session['vards'] = lietotajs['vards']
            return redirect('/izvelne')

        else:
            return "Nepareizi dati"

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():

    if  request.method == 'POST':
        epasts = request.form.get('epasts')
        vards = request.form.get('vards')
        uzvards = request.form.get('uzvards')
        klase = request.form.get('klase')
        parole = request.form.get('parole')
        parole_hash = generate_password_hash(parole)

        conn = sqlite3.connect("datubaze.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO users (epasts, vards, uzvards, klase, parole)
        VALUES (?, ?, ?, ?, ?)
        """, (epasts, vards, uzvards, klase, parole_hash))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')


@app.route("/izvelne")
def izvelne():

    conn = sqlite3.connect("datubaze.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM pulcini")
    pulcini = cur.fetchall()
    conn.close()

    return render_template("izvelne.html" , pulcini=pulcini)


@app.route("/pieteikumi")
def pieteikumi():
    return render_template("pieteikumi.html")


@app.route('/admin')
def admin():

    conn = sqlite3.connect("datubaze.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM pulcini")
    pulcini = cur.fetchall()
    cur.execute("""
    SELECT pieteikumi.id, users.vards, users.uzvards, users.klase, pulcini.nosaukums
    FROM pieteikumi
    JOIN users ON pieteikumi.user_id = users.id
    JOIN pulcini ON pieteikumi.pulcins_id = pulcini.id
    """)
    pieteikumi = cur.fetchall()
    conn.close()

    return render_template('admin.html', pulcini=pulcini, pieteikumi=pieteikumi)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
	app.run(debug=True)