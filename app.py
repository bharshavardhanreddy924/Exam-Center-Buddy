import re
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/hallticketapp"
mongo = PyMongo(app)

def normalize_center(center_str):
    """
    Normalize the exam center string by removing symbols,
    trimming whitespace and converting to uppercase.
    """
    normalized = re.sub(r'[^A-Za-z0-9 ]+', '', center_str).strip().upper()
    return normalized

# Landing page
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username    = request.form.get('username')
        password    = request.form.get('password')
        name        = request.form.get('name')
        roll_number = request.form.get('roll_number')
        phone       = request.form.get('phone')
        
        # Determine exam center from dropdown vs. other
        exam_center_select = request.form.get('exam_center_select')
        if exam_center_select == 'other':
            exam_center_raw = request.form.get('exam_center_other')
        else:
            exam_center_raw = exam_center_select

        # Normalize the exam center string
        normalized_center = normalize_center(exam_center_raw)

        # Check if username already exists
        if mongo.db.users.find_one({'username': username}):
            flash('Username already exists. Please choose another one.', 'danger')
            return redirect(url_for('register'))
        
        user_data = {
            'username': username,
            'password': generate_password_hash(password),
            'name': name,
            'roll_number': roll_number,
            'phone': phone,
            'exam_center': normalized_center,
            'available': False,  # default availability is False
            'registered_at': datetime.now()
        }
        mongo.db.users.insert_one(user_data)
        
        # Add exam center if it does not exist
        if not mongo.db.centers.find_one({'name': normalized_center}):
            center_data = {'name': normalized_center, 'created_at': datetime.now()}
            mongo.db.centers.insert_one(center_data)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    # Get centers from database for dropdown (if any)
    centers = list(mongo.db.centers.find())
    return render_template('register.html', centers=centers)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = mongo.db.users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Toggle availability route
@app.route('/toggle_availability', methods=['POST'])
def toggle_availability():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = mongo.db.users.find_one({'username': session['username']})
    new_status = not user.get('available', False)
    mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'available': new_status}})
    flash(f'Your availability status has been set to {"Available" if new_status else "Not Available"}.', 'success')
    return redirect(url_for('dashboard'))

# Dashboard route (only shows same center students who are available)
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'username': session['username']})
    # Find students at the same exam center (excluding the current user) who are available
    same_center_students = list(mongo.db.users.find({
        'exam_center': user['exam_center'],
        'username': {'$ne': session['username']},
        'available': True
    }))
    
    return render_template('dashboard.html', user=user, same_center_students=same_center_students)

if __name__ == '__main__':
    app.run(debug=True)
