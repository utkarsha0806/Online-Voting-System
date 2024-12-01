from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
import cv2
from datetime import datetime
import face_recognition

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key_here'
# ... Define your routes and other Flask configurations here ...

known_face_encoding = None
captured_face_encoding = None
results = None
first_face_encoding = None


def get_conn():
    
    db = sqlite3.connect("data.db")

    return db

db = get_conn()
cursor = db.cursor()
cursor.execute('''
            CREATE TABLE IF NOT EXISTS faceData (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                face_id INTERGER  UNIQUE NOT NULL
            )
        ''')
db.commit()
cursor.execute('''
            CREATE TABLE IF NOT EXISTS register (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first TEXT UNIQUE NOT NULL,
                last TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT UNIQUE NOT NULL,
                con_password TEXT UNIQUE NOT NULL
            )
        ''')
db.commit()
cursor.execute('''
            CREATE TABLE IF NOT EXISTS vote (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                user_vote TEXT UNIQUE
            )
        ''')
db.commit()
db.close()

@app.route('/get_image/<path:filename>')
def get_image(filename):
    return send_from_directory('Face_img', filename)


@app.route('/ved')
def index2():
    return render_template("index2.html")

# Folder to store face images
UPLOAD_FOLDER = 'Face_img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# HTML page for face capture
@app.route('/face')
def face():
    return render_template('face.html')

# Route to handle face capture
@app.route('/capture', methods=['POST'])
def capture():
    
    try:
        # Get the image file from the request
        image_file = request.files['imageData']
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        filename = f'captured_face_{timestamp}.png'
        # Save the image file to the specified folder
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        
        email = session.get('email')

        if not email:
            return "Email not found in session", 400
        
        db = get_conn()
        cursor = db.cursor()
        q = '''
            INSERT INTO faceData (email,face_id)
            VALUES (?, ?)
        '''
        cursor.execute(q,(email,timestamp))
        db.commit()
        db.close()

        return redirect(url_for('home'))
    except Exception as e:
        return str(e), 500
    


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit3', methods=['POST'])
def submit3():
    if request.method == 'POST':
        # Process other form fields

        # Get the image data from the request
        image_data = request.form.get('imageData')

        # Save the image data to a file or database
        # You might want to use a library like base64 to decode the image data
        # Save the decoded image to a file or store it in the database
        # Example: `with open('user_images/user123.jpg', 'wb') as f: f.write(decoded_image)`

    return redirect(url_for('home'))



@app.route('/compare_faces', methods=['POST'])
def compare_faces():
    global first_face_encoding
    # Get the captured image and reference image from the request
    captured_image = request.files['imageData']
    reference_image = request.files['referenceImage']

    # Load the captured and reference images using face_recognition
    captured_image_data = face_recognition.load_image_file(captured_image)
    reference_image_data = face_recognition.load_image_file(reference_image)

    # Get the face encodings from both images
    reference_face_encoding = face_recognition.face_encodings(reference_image_data)[0]
    # captured_face_encoding = face_recognition.face_encodings(captured_image_data)[0]
    captured_face_encoding = face_recognition.face_encodings(captured_image_data)
    if captured_face_encoding:
        # Proceed with using the face encoding
        first_face_encoding = captured_face_encoding[0]
    else:
        # Handle the case when no face is found in the image
        # You might want to return an error message or handle it accordingly
        return "Picture is not clear, RETAKE IMAGE"


    # Compare the face encodings to determine similarity
    results = face_recognition.compare_faces([reference_face_encoding], first_face_encoding, tolerance=0.6)

    # Return the comparison result to the client
    if results[0]:
        session['result'] = True
        return "Faces match"
    else:
        return "Faces do not match"


@app.route('/valid_face')
def valid_face():
    
    email = session.get('email')

    if not email:
        return "Email not found in session", 400

    db = get_conn()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM faceData WHERE email=?", (email,))
    entries = cursor.fetchall()
    db.commit()
    db.close()
    return render_template("validate_face.html",entries=entries)


@app.route("/submit",methods=['POST'])
def submit():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_conn()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM register")
        entries = cursor.fetchall()
        db.commit()
        db.close()
        for i in range(len(entries)):
            if username == f"{entries[i][3]}" and password== f"{entries[i][4]}":
                session['email'] = f"{entries[i][3]}"
                return redirect(url_for('valid_face'))
        else:
            msg="Login Invalid"
            return render_template('index.html', msg=msg)

@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/submit2', methods=['POST'])
def submit2():

    if request.method == 'POST':
        first = request.form['first']
        last = request.form['last']
        password = request.form['password']
        con_password = request.form['con_password']
        email = request.form['email']
        session['email'] = email  
        
        db = get_conn()
        cursor = db.cursor()
        q = '''
            INSERT INTO register (first, last, email, password, con_password)
            VALUES (?, ?, ?, ?,?)
        '''
        cursor.execute(q,(first, last, email, password,con_password))
        db.commit()
        db.close()  

    return redirect("/face")


@app.route('/vote')
def vote():
    if session['result']:
        return render_template("vote.html")
    else:
        return redirect("/")

@app.route('/voted', methods=['POST'])
def voted():
    if 'email' not in session:
        return redirect(url_for('home'))

    voter_email = session.get('email')
    selected_candidate = request.form.get('candidate')

    db = get_conn()
    cursor = db.cursor()

    # Check if the user has already voted
    cursor.execute("SELECT * FROM vote WHERE email=?", (voter_email,))
    existing_vote = cursor.fetchone()

    if existing_vote:
        return render_template('error.html', message='You have already voted.')

    # Insert the vote into the vote table
    cursor.execute("INSERT INTO vote (email, user_vote) VALUES (?, ?)", (voter_email, selected_candidate))
    db.commit()

    db.close()

    return redirect(url_for('votedList'))

@app.route('/vote_result')
def votedResult():
    db = get_conn()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM vote")
    votes = cursor.fetchall()
    db.commit()
# Count votes for each candidate
    cursor.execute("SELECT user_vote, COUNT(*) as count FROM vote GROUP BY user_vote")
    vote_counts = dict(cursor.fetchall())

    # Find the winner
    winner = max(vote_counts, key=vote_counts.get)
    db.commit()
    db.close()
    
    return render_template("vote_result.html", votes=votes, winner=winner)


@app.route('/voted_list')
def votedList():
    db = get_conn()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM vote")
    votes = cursor.fetchall()
    db.commit()
    db.close()
    
    return render_template("voted_list.html", votes=votes)



if __name__ == '__main__':
    app.run(debug=True)
