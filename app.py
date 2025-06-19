from flask import Flask, render_template, request, redirect, url_for, session
import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from extract_docx_with_images import extract_text_and_images
from db import get_connection
from datetime import timedelta

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx'}

app = Flask(__name__)
app.secret_key = 'cheie_secreta_sigura'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.permanent_session_lifetime = timedelta(days=7)

os.makedirs('uploads', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    conn = get_connection()
    cur = conn.cursor()
    
    if q:
        cur.execute("SELECT id, titlu, continut FROM articole WHERE LOWER(titlu) LIKE %s ORDER BY id DESC", (f'%{q.lower()}%',))
    else:
        cur.execute("SELECT id, titlu, continut FROM articole ORDER BY id DESC")
    articole = cur.fetchall()
    
    # Obține toate etichetele pentru afișare
    cur.execute("SELECT id, nume FROM etichete ORDER BY nume")
    toate_etichetele = cur.fetchall()
    
    cur.close()
    conn.close()
    
    tag_cautat = request.args.get('tag', '')
    return render_template('index.html', articole=articole, toate_etichetele=toate_etichetele, tag_cautat=tag_cautat)

@app.route('/articol/<int:articol_id>')
def articol(articol_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT titlu, continut FROM articole WHERE id = %s", (articol_id,))
    articol = cur.fetchone()
    
    # Obține etichetele articolului
    cur.execute("""
        SELECT e.id, e.nume 
        FROM etichete e
        JOIN articole_etichete ae ON e.id = ae.eticheta_id
        WHERE ae.articol_id = %s
        ORDER BY e.nume
    """, (articol_id,))
    etichete = cur.fetchall()
    
    cur.close()
    conn.close()
    
    if articol:
        return render_template('articol.html', articol=articol, etichete=etichete, articol_id=articol_id)
    return "Articolul nu a fost găsit.", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        parola = request.form['password']

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT parola FROM utilizatori WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[0], parola):
            session['logged_in'] = True
            if 'remember' in request.form:
                session.permanent = True
            return redirect(url_for('index'))
        else:
            error = 'Date de autentificare incorecte.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        titlu = request.form['titlu']
        fisier = request.files['fisier']
        if fisier and allowed_file(fisier.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(fisier.filename)}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            fisier.save(path)
            continut = extract_text_and_images(path)
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO articole (titlu, continut) VALUES (%s, %s)", (titlu, continut))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/edit/<int:articol_id>', methods=['GET', 'POST'])
def edit(articol_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT titlu FROM articole WHERE id = %s", (articol_id,))
    rezultat = cur.fetchone()
    cur.close()
    conn.close()

    if not rezultat:
        return "Articol inexistent", 404

    titlu = rezultat[0]

    if request.method == 'POST':
        fisier = request.files['fisier']
        if fisier and allowed_file(fisier.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(fisier.filename)}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            fisier.save(path)
            continut = extract_text_and_images(path)
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE articole SET continut = %s WHERE id = %s", (continut, articol_id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', titlu=titlu)

@app.route('/delete/<int:articol_id>')
def delete(articol_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM articole WHERE id = %s", (articol_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_tag/<int:articol_id>', methods=['GET', 'POST'])
def add_tag(articol_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        nume_eticheta = request.form['nume_eticheta'].strip().lower()
        if nume_eticheta:
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute("INSERT INTO etichete (nume) VALUES (%s) ON CONFLICT (nume) DO UPDATE SET nume = EXCLUDED.nume RETURNING id", (nume_eticheta,))
            eticheta_id = cur.fetchone()[0]
            
            cur.execute("INSERT INTO articole_etichete (articol_id, eticheta_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (articol_id, eticheta_id))
            
            conn.commit()
            cur.close()
            conn.close()
        
        return redirect(url_for('articol', articol_id=articol_id))

    return render_template('add_tag.html', articol_id=articol_id)

@app.route('/remove_tag/<int:articol_id>/<int:eticheta_id>')
def remove_tag(articol_id, eticheta_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM articole_etichete WHERE articol_id = %s AND eticheta_id = %s", (articol_id, eticheta_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('articol', articol_id=articol_id))

@app.route('/search_by_tag')
def search_by_tag():
    tag = request.args.get('tag', '').strip().lower()
    if not tag:
        return redirect(url_for('index'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.titlu, a.continut 
        FROM articole a
        JOIN articole_etichete ae ON a.id = ae.articol_id
        JOIN etichete e ON ae.eticheta_id = e.id
        WHERE e.nume = %s
        ORDER BY a.id DESC
    """, (tag,))
    articole = cur.fetchall()
    
    cur.execute("SELECT id, nume FROM etichete ORDER BY nume")
    toate_etichetele = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('index.html', articole=articole, toate_etichetele=toate_etichetele, tag_cautat=tag)

if __name__ == '__main__':
    app.run(debug=True)