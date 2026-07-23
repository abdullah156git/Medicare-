import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'super_secret_admin_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",         
        password="1234",# 
        database="pharma_db"  
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == '1234':
            session['is_admin'] = True
            return redirect(url_for('index'))
        elif username == 'abd' and password == '1234':
            session['is_admin'] = True
            return redirect(url_for('index'))    
        else:
            return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))


@app.route('/')
def index():
    is_admin = session.get('is_admin', False)
    return render_template('index.html', is_admin=is_admin)

@app.route('/add')
def add_page():
    if not session.get('is_admin'): return redirect(url_for('login'))
    return render_template('add.html')

@app.route('/edit_list')
def edit_list_page():
    if not session.get('is_admin'): return redirect(url_for('login'))
    return render_template('edit_list.html')

@app.route('/edit/<int:med_id>')
def edit_page(med_id):
    if not session.get('is_admin'): return redirect(url_for('login'))
    return render_template('edit.html', med_id=med_id)



@app.route('/api/add_medicine', methods=['POST'])
def add_medicine():
    if not session.get('is_admin'): return jsonify({"error": "Unauthorized"}), 401
    try:
        name = request.form.get('name')
        storing_details = request.form.get('storing_details')
        description = request.form.get('description')
        use_of_medication = request.form.get('use_of_medication')
        side_effects = request.form.get('side_effects')
        allergy_warning = request.form.get('allergy_warning')
        how_to_use = request.form.get('how_to_use')
        external_links = request.form.get('external_links')
        similar_ids = request.form.get('similar_ids')
        
        images = request.files.getlist('images')
        image_paths = []
        for image in images:
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_paths.append(f"uploads/{filename}")
        
        image_paths_str = ",".join(image_paths)

        db = get_db_connection()
        cursor = db.cursor()

        sql = """INSERT INTO medicines 
                 (name, storing_details, description, use_of_medication, side_effects, allergy_warning, how_to_use, external_links, image_paths) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (name, storing_details, description, use_of_medication, side_effects, allergy_warning, how_to_use, external_links, image_paths_str)
        cursor.execute(sql, val)
        medicine_id = cursor.lastrowid

        if similar_ids:
            sim_ids = [int(id.strip()) for id in similar_ids.split(',') if id.strip().isdigit()]
            for sim_id in sim_ids:
                cursor.execute("INSERT INTO similar_medicines (medicine_id, similar_medicine_id) VALUES (%s, %s)", (medicine_id, sim_id))

        db.commit()
        return jsonify({"message": "Medicine added successfully", "id": medicine_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()

@app.route('/api/edit_medicine/<int:med_id>', methods=['POST'])
def edit_medicine(med_id):
    if not session.get('is_admin'): return jsonify({"error": "Unauthorized"}), 401
    try:
        name = request.form.get('name')
        storing_details = request.form.get('storing_details')
        description = request.form.get('description')
        use_of_medication = request.form.get('use_of_medication')
        side_effects = request.form.get('side_effects')
        allergy_warning = request.form.get('allergy_warning')
        how_to_use = request.form.get('how_to_use')
        external_links = request.form.get('external_links')
        similar_ids = request.form.get('similar_ids')

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT image_paths FROM medicines WHERE id = %s", (med_id,))
        existing_med = cursor.fetchone()
        image_paths_str = existing_med['image_paths'] if existing_med else ""

        images = request.files.getlist('images')
        new_image_paths = []
        for image in images:
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_image_paths.append(f"uploads/{filename}")
        
        if new_image_paths:
            image_paths_str = ",".join(new_image_paths)

        sql = """UPDATE medicines 
                 SET name=%s, storing_details=%s, description=%s, use_of_medication=%s, side_effects=%s, allergy_warning=%s, how_to_use=%s, external_links=%s, image_paths=%s 
                 WHERE id=%s"""
        val = (name, storing_details, description, use_of_medication, side_effects, allergy_warning, how_to_use, external_links, image_paths_str, med_id)
        cursor.execute(sql, val)

        cursor.execute("DELETE FROM similar_medicines WHERE medicine_id = %s", (med_id,))
        if similar_ids:
            sim_ids = [int(id.strip()) for id in similar_ids.split(',') if id.strip().isdigit()]
            for sim_id in sim_ids:
                cursor.execute("INSERT INTO similar_medicines (medicine_id, similar_medicine_id) VALUES (%s, %s)", (med_id, sim_id))

        db.commit()
        return jsonify({"message": "Medicine updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()

@app.route('/api/delete_medicine/<int:med_id>', methods=['DELETE'])
def delete_medicine(med_id):
    if not session.get('is_admin'): return jsonify({"error": "Unauthorized"}), 401
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT image_paths FROM medicines WHERE id = %s", (med_id,))
        med = cursor.fetchone()
        
        cursor.execute("DELETE FROM medicines WHERE id = %s", (med_id,))
        db.commit()
        
        if med and med['image_paths']:
            paths = med['image_paths'].split(',')
            for path in paths:
                full_image_path = os.path.join(app.root_path, 'static', path)
                if os.path.exists(full_image_path):
                    os.remove(full_image_path)
                
        return jsonify({"message": "Medicine deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()

@app.route('/api/search', methods=['GET'])
def search_medicine():
    query = request.args.get('q', '')
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name, image_paths FROM medicines WHERE name LIKE %s", ('%' + query + '%',))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(results)

@app.route('/api/medicine/<int:med_id>', methods=['GET'])
def get_medicine(med_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicines WHERE id = %s", (med_id,))
    medicine = cursor.fetchone()
    
    if not medicine:
        return jsonify({"error": "Medicine not found"}), 404

    medicine['images'] = medicine['image_paths'].split(',') if medicine['image_paths'] else []

    cursor.execute("""
        SELECT m.id, m.name, m.image_paths 
        FROM similar_medicines sm
        JOIN medicines m ON sm.similar_medicine_id = m.id
        WHERE sm.medicine_id = %s
    """, (med_id,))
    medicine['similar_medicines'] = cursor.fetchall()
    medicine['similar_ids_raw'] = ",".join([str(m['id']) for m in medicine['similar_medicines']])

    cursor.close()
    db.close()
    return jsonify(medicine)

if __name__ == '__main__':
    app.run(debug=True)