from flask import Flask, render_template, request, redirect, url_for , session, flash
import random
import sqlite3
from werkzeug.security import generate_password_hash , check_password_hash


app = Flask(__name__)
app.secret_key = "slepenais"

# Savienojums ar datubāzi
def get_db():
    return sqlite3.connect("datubaze.db")


@app.route("/") # Sākumlapa
def home():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST']) # Pieslēgšanās
def login():

    if request.method == 'POST':
        epasts = request.form.get('epasts')
        parole = request.form.get('parole')

        if epasts == "" or parole == "":
            flash("Aizpildi visus laukus")
            return redirect('/login')

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


@app.route('/register', methods=['GET', 'POST']) # Reģistrācija
def register():

    if  request.method == 'POST':
        epasts = request.form.get('epasts')
        vards = request.form.get('vards')
        uzvards = request.form.get('uzvards')
        klase = request.form.get('klase')
        parole = request.form.get('parole')
        parole_hash = generate_password_hash(parole)

        if epasts == "" or vards == "" or uzvards == "" or klase == "" or parole == "":
            flash("Visi lauki obligāti jāaizpilda")
            return redirect('/register')

        if "@edu.riga.lv" not in epasts:
            flash("Ievadi skolas epastu - @edu.riga.lv")
            return redirect('/register')

        conn = sqlite3.connect("datubaze.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE epasts = ?", (epasts,))
        parbaude = cur.fetchone()

        if parbaude:
            conn.close()
            flash("Tu jau esi reģistrējies ar šo epastu!")
            return redirect('/register')

        cur.execute("""
        INSERT INTO users (epasts, vards, uzvards, klase, parole)
        VALUES (?, ?, ?, ?, ?)
        """, (epasts, vards, uzvards, klase, parole_hash))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')


@app.route("/izvelne") # Skolēna pulciņu saraksts
def izvelne():

    if not session.get('id'):
        return redirect('/login')
    
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


@app.route('/pievienoties', methods=['POST']) # Pieteikšanās pulciņam
def pievienoties():

    user_id = session.get('id')
    pulcins_id = request.form.get('pulcins_id')
    conn = sqlite3.connect("datubaze.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM pulcini WHERE id = ?", (pulcins_id,))
    pulcins = cur.fetchone()

    if pulcins[3] <= 0:
        conn.close()
        flash("Pulciņš ir pilns")
        return redirect('/izvelne')

    cur.execute("SELECT * FROM pieteikumi WHERE user_id = ? AND pulcins_id = ?", (user_id, pulcins_id))
    atbilde = cur.fetchone()

    if atbilde:
        conn.close()
        flash("Tu jau esi pieteicies")
        return redirect('/izvelne')

    cur.execute("SELECT vietas FROM pulcini WHERE id = ?", (pulcins_id,))
    vietas = cur.fetchone()

    if vietas and vietas[0] > 0 and not atbilde:

        cur.execute("INSERT INTO pieteikumi (user_id, pulcins_id) VALUES (?, ?)", (user_id, pulcins_id))
        cur.execute("UPDATE pulcini SET vietas = vietas - 1 WHERE id = ?", (pulcins_id,))
        conn.commit()

    conn.close()

    return redirect('/izvelne')


@app.route("/pieteikumi") # Skolēna pieteikumi
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


@app.route('/atteikties', methods=['POST']) # Atteikties no pulciņa
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


@app.route('/admin') # Admin / Skolotāja panelis
def admin():

    if session.get('loma') != 'admin':
        return redirect('/')

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


@app.route('/admin_izveidot', methods=['GET', 'POST']) # Izveidot pulciņu
def admin_izveidot():

    if session.get('loma') != 'admin':
        return redirect('/')

    if request.method == 'POST':

        nosaukums = request.form.get('nosaukums')
        apraksts = request.form.get('apraksts')
        vietas = request.form.get('vietas')

        if nosaukums == "" or apraksts == "" or vietas == "":
            flash("Visi lauki jāaizpilda")
            return redirect('/admin_izveidot')

        if int(vietas) <= 0:
            flash("Vietu skaits nevar būt negatīvs vai 0")
            return redirect('/admin_izveidot')

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


@app.route('/admin_delete', methods=['POST']) # Dzēst pulciņu
def admin_delete():

    if session.get('loma') != 'admin':
        return redirect('/')

    pulcins_id = request.form.get('id')
    conn = sqlite3.connect("datubaze.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM pieteikumi WHERE pulcins_id = ?", (pulcins_id,))
    cur.execute("DELETE FROM pulcini WHERE id = ?", (pulcins_id,))
    conn.commit()
    conn.close()

    return redirect('/admin')


@app.route("/logout") # Iziet no konta
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
	app.run(debug=True)