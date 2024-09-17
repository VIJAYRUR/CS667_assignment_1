from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import random
import string
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import bcrypt
app = Flask(__name__)
app.secret_key = "secret_key"  # Required for session management

# In-memory store for OTPs, in a real app use a database
otp_store = {}

# MongoDB Atlas connection string
client = MongoClient('mongodb+srv://Vijay:SanjayN@cluster0.htlbk.mongodb.net/my_app_db?retryWrites=true&w=majority')
db = client['my_app_db']

users_collection = db['users']
courses_collection = db['courses']
enrollments_collection = db['enrollments']

# Configure email
EMAIL_ADDRESS = 'proconnect522@gmail.com@'
EMAIL_PASSWORD = 'swie gaic lzwt ojfc'


@app.route('/')
def home():
    if 'email' in session:
        return redirect(url_for('courses'))
    return render_template('home.html')

@app.route('/courses')
def courses():
    if 'email' in session:
        return redirect(url_for('courses'))
    return render_template('home.html')



@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        # Hash the password
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())


        # Insert new user into the users collection
        users_collection.insert_one({'name': name, 'email': email, 'password': hashed_password})

        return redirect(url_for('login'))
    return render_template('register.html')

def send_email(recipient_email, otp):
    sender_email = EMAIL_ADDRESS
    sender_password = EMAIL_PASSWORD
    subject = 'Your OTP Code'
    body = f"Your OTP code is {otp}. Please use this to verify your login attempt."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/generate_otp', methods=['POST'])
def generate_otp():
    email = request.form['edu-email'] + '@horizon.csueastbay.edu'
    otp = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    otp_store[email] = otp
    send_email(email, otp)  # Send OTP via email
    return jsonify({'message': 'OTP has been generated and sent to your email!', 'otp_required': True})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['edu-email'] + '@horizon.csueastbay.edu'
        netid = request.form['netid']
        otp = request.form.get('otp')

        # Check if OTP is provided and valid
        if otp:
            if otp_store.get(email) == otp:
                # Check if user exists
                user = users_collection.find_one({'email': email})

                if not user:
                    # If user does not exist, insert the new user details
                    users_collection.insert_one({
                        'email': email,
                        'netid': netid,
                        'last_login': datetime.now()
                    })
                else:
                    # If user exists, update the netid and last login time
                    users_collection.update_one(
                        {'email': email},
                        {'$set': {
                            'netid': netid,
                            'last_login': datetime.now()
                        }}
                    )
                
                # Successful login, store session information or render next page
                session['email'] = email
                return render_template('courses.html')
            else:
                flash('Invalid OTP. Please try again.', 'danger')
                return render_template('login.html')
        else:
            flash('OTP is required.', 'warning')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove 'email' from the session
    return redirect(url_for('login'))  # Redirect to the login page or home page


@app.route('/enroll/<course_id>')
def enroll(course_id):
    if 'email' in session:
        user = users_collection.find_one({'email': session['email']})
        course = courses_collection.find_one({'_id': ObjectId(course_id)})
        
        enrollments_collection.insert_one({
            'user_id': user['_id'],
            'course_id': course['_id'],
            'enrolled_on': '2024-09-10'
        })
        return f'You have successfully enrolled in {course["title"]}'
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
