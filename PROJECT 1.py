from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

# Attendance model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='attendances')

User.attendances = db.relationship('Attendance', back_populates='user')

# Create the database
with app.app_context():
    db.create_all()

# HTML Templates
login_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h2>Login</h2>
        <form method="POST">
            <div>
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div>
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <ul>
            {% for category, message in messages %}
                <li>{{ message }}</li>
            {% endfor %}
            </ul>
        {% endif %}
        {% endwith %}
    </div>
</body>
</html>
'''

dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h2>Welcome, {{ user.username }}!</h2>
        <a href="{{ url_for('mark_attendance') }}">Mark Attendance</a>
        <h3>Attendance Records</h3>
        <table>
            <tr>
                <th>Date</th>
                <th>Status</th>
            </tr>
            {% for record in attendances %}
                <tr>
                    <td>{{ record.date }}</td>
                    <td>{{ record.status }}</td>
                </tr>
            {% endfor %}
        </table>
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>
</body>
</html>
'''

attendance_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mark Attendance</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h2>Mark Attendance</h2>
        <form method="POST">
            <div>
                <label for="date">Date:</label>
                <input type="date" id="date" name="date" required>
            </div>
            <div>
                <label for="status">Status:</label>
                <select id="status" name="status" required>
                    <option value="Present">Present</option>
                    <option value="Absent">Absent</option>
                </select>
            </div>
            <button type="submit">Submit</button>
        </form>
    </div>
</body>
</html>
'''

style_css = '''
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f4f4f4;
}

.container {
    width: 400px;
    margin: 100px auto;
    background-color: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

h2, h3 {
    text-align: center;
}

form div {
    margin: 10px 0;
}

input, select, button {
    width: 100%;
    padding: 10px;
    margin: 5px 0;
}

button {
    background-color: #4CAF50;
    color: white;
    border: none;
    cursor: pointer;
}

button:hover {
    background-color: #45a049;
}

a {
    display: block;
    text-align: center;
    margin-top: 20px;
    text-decoration: none;
    color: #333;
}

a:hover {
    color: #007BFF;
}
'''

# Routes

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    return render_template_string(login_html)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    attendances = Attendance.query.filter_by(user_id=user.id).all()
    return render_template_string(dashboard_html, user=user, attendances=attendances)

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        status = request.form['status']
        date = request.form['date']
        new_attendance = Attendance(date=date, status=status, user_id=user.id)
        db.session.add(new_attendance)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template_string(attendance_html)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Serve the static CSS file
    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)
    
    # Create the database if it doesn't exist
    with app.app_context():
        db.create_all()

    app.run(debug=True)
