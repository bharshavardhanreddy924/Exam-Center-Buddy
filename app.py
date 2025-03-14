import os
import re
import certifi
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# MongoDB Configuration
uri = "mongodb+srv://bharshavardhanreddy924:516474Ta@data-dine.5oghq.mongodb.net/?retryWrites=true&w=majority&ssl=true"
client = MongoClient(uri, tlsCAFile=certifi.where())

db = client['hallticketapp']

# Function to normalize exam center
def normalize_center(center_str):
    return re.sub(r'[^A-Za-z0-9 ]+', '', center_str).strip().upper()

# Landing Page
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        roll_number = request.form.get('roll_number')
        phone = request.form.get('phone')
        
        exam_center_select = request.form.get('exam_center_select')
        exam_center_raw = request.form.get('exam_center_other') if exam_center_select == 'other' else exam_center_select
        normalized_center = normalize_center(exam_center_raw)
        
        if db.users.find_one({'username': username}):
            flash('Username already exists. Please choose another one.', 'danger')
            return redirect(url_for('register'))
        
        user_data = {
            'username': username,
            'password': generate_password_hash(password),
            'name': name,
            'roll_number': roll_number,
            'phone': phone,
            'exam_center': normalized_center,
            'available': False,
            'registered_at': datetime.now()
        }
        db.users.insert_one(user_data)
        
        if not db.centers.find_one({'name': normalized_center}):
            db.centers.insert_one({'name': normalized_center, 'created_at': datetime.now()})
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    centers = list(db.centers.find())
    return render_template('register.html', centers=centers)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Toggle Availability Route
@app.route('/toggle_availability', methods=['POST'])
def toggle_availability():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = db.users.find_one({'username': session['username']})
    new_status = not user.get('available', False)
    db.users.update_one({'_id': user['_id']}, {'$set': {'available': new_status}})
    flash(f'Your availability status has been set to {"Available" if new_status else "Not Available"}.', 'success')
    return redirect(url_for('dashboard'))

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = db.users.find_one({'username': session['username']})
    same_center_students = list(db.users.find({
        'exam_center': user['exam_center'],
        'username': {'$ne': session['username']},
        'available': True
    }))
    
    return render_template('dashboard.html', user=user, same_center_students=same_center_students)

# Deployment Configuration
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
