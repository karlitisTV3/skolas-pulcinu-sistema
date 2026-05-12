from flask import Flask, render_template, request, redirect, url_for , session, flash
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
            session['loma'] = lietotajs['loma']
    
            if lietotajs['loma'] == 'admin':
                return redirect('/admin')

            elif lietotajs['loma'] == 'student':
                return redirect('/izvelne')

            else:
                flash('Nepareizi dati!')
                return redirect('login')

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

    user_id = session.get('id')
    conn = sqlite3.connect("datubaze.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM pulcini")
    pulcini = cur.fetchall()

    cur.execute("SELECT pulcins_id FROM pieteikumi WHERE user_id = ?", (user_id,))
    mani = [m["pulcins_id"] for m in cur.fetchall()]
    conn.close()

    return render_template("izvelne.html" , pulcini=pulcini , mani=mani)


@app.route('/pievienoties', methods=['POST'])
def pievienoties():

    user_id = session.get('id')
    pulcins_id = request.form.get('pulcins_id')
    conn = sqlite3.connect("datubaze.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM pieteikumi WHERE user_id = ? AND pulcins_id = ?", (user_id, pulcins_id))
    atbilde = cur.fetchone()

    cur.execute("SELECT vietas FROM pulcini WHERE id = ?", (pulcins_id,))
    vietas = cur.fetchone()

    if vietas and vietas[0] > 0 and not atbilde:

        cur.execute("INSERT INTO pieteikumi (user_id, pulcins_id) VALUES (?, ?)", (user_id, pulcins_id))
        cur.execute("UPDATE pulcini SET vietas = vietas - 1 WHERE id = ?", (pulcins_id,))
        conn.commit()

    conn.close()

    return redirect('/izvelne')


@app.route("/pieteikumi")
def pieteikumi():

    user_id = session.get('id')
    conn = sqlite3.connect("datubaze.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    SELECT pulcini.id, pulcini.nosaukums
    FROM pieteikumi
    JOIN pulcini ON pieteikumi.pulcins_id = pulcini.id
    WHERE pieteikumi.user_id = ?
    """, (user_id,))

    pieteikumi = cur.fetchall()
    conn.close()

    return render_template("pieteikumi.html", pieteikumi=pieteikumi)


@app.route('/atteikties', methods=['POST'])
def atteikties():

    user_id = session.get('id')
    pulcins_id = request.form.get('pulcins_id')

    if not pulcins_id:
        return redirect('/pieteikumi')

    conn = sqlite3.connect("datubaze.db", timeout=10)
    cur = conn.cursor()

    cur.execute("DELETE FROM pieteikumi WHERE user_id = ? AND pulcins_id = ?", (user_id, pulcins_id))
    cur.execute("UPDATE pulcini SET vietas = vietas + 1 WHERE id = ?", (pulcins_id,))

    conn.commit()
    conn.close()

    return redirect('/pieteikumi')


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


@app.route('/admin_izveidot', methods=['GET', 'POST'])
def admin_izveidot():

    if request.method == 'POST':

        nosaukums = request.form.get('nosaukums')
        apraksts = request.form.get('apraksts')
        vietas = request.form.get('vietas')

        conn = sqlite3.connect("datubaze.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO pulcini (nosaukums, apraksts, vietas)
        VALUES (?, ?, ?)
        """, (nosaukums, apraksts, vietas))

        conn.commit()
        conn.close()

        return redirect('/admin')

    return render_template('admin_izveidot.html')


@app.route('/admin_delete', methods=['POST'])
def admin_delete():

    pulcins_id = request.form.get('id')
    conn = sqlite3.connect("datubaze.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM pieteikumi WHERE pulcins_id = ?", (pulcins_id,))
    cur.execute("DELETE FROM pulcini WHERE id = ?", (pulcins_id,))
    conn.commit()
    conn.close()

    return redirect('/admin')


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
	app.run(debug=True)