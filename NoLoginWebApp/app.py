'''
D.B.
9-25-24
This code is similar to the 'Web App' code. It has an additional "home" page (/) that allows document upload and quiz generation without login.
'''


from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime
from mcq_to_json import generate_questions, extract_text_from_pdf, save_questions_to_csv
import csv


# Define application
app = Flask(__name__)

# Absolute path for the database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(BASE_DIR, 'instance')

# Ensure the instance directory exists
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Configuration
app.config['SECRET_KEY'] = 'e5f6c1d6f8e9134b2246a4c7ea1a6f72' 
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "site.db")}'
app.config['SQLALCHEMY_BINDS'] = {
    'pdf_db': f'sqlite:///{os.path.join(instance_path, "pdf_data.db")}'
}

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# PDF Upload Folder
UPLOAD_FOLDER = 'static/pdfs'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User model for login
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    assignments = db.relationship('Assignment', backref='assigned_user', lazy=True)

# Assignment model for quiz handling
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdf_path = db.Column(db.String(120), nullable=False)
    quiz_path = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#--- Bind PDFData model to a separate database ---#
class PDFData(db.Model):
    __bind_key__ = 'pdf_db'  # Bind to the separate database for PDFs
    id = db.Column(db.Integer, primary_key=True)
    pdf_path = db.Column(db.String(120), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
#--- End ---#

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# PDF upload and quiz generation route
@app.route('/upload_and_generate_quiz', methods=['POST'])
def upload_and_generate_quiz():
    try:
        pdf_file = request.files.get('pdf_file')
        if not pdf_file:
            flash('No file uploaded', 'danger')
            return redirect(url_for('home'))

        # Save the file
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
        pdf_file.save(pdf_path)

        # Process the PDF
        extracted_text = extract_text_from_pdf(pdf_path)

        # Generate questions based on the extracted text
        questions_text = generate_questions(extracted_text)

        # Ensure the quizzes directory exists
        quizzes_dir = 'static/quizzes'
        if not os.path.exists(quizzes_dir):
            os.makedirs(quizzes_dir)

        # Save the questions to a CSV file
        quiz_filename = f'{pdf_file.filename}_quiz.csv'
        csv_path = os.path.join(quizzes_dir, quiz_filename)
        save_questions_to_csv(questions_text, csv_path)

        # Redirect to the new quiz page with the CSV path
        return redirect(url_for('display_quiz', quiz_path=quiz_filename))
    except Exception as e:
        print(f"Error during PDF upload: {e}")
        flash('An error occurred during PDF upload.', 'danger')
        return redirect(url_for('home'))

# Display quiz
@app.route('/display_quiz/<quiz_path>', methods=['GET', 'POST'])
def display_quiz(quiz_path):
    quiz_full_path = os.path.join('static/quizzes', quiz_path)

    if request.method == 'POST':
        # Process the quiz submission
        selected_answers = request.form.to_dict()
        correct_answers = 0
        total_questions = 0
        questions_data = []

        with open(quiz_full_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                total_questions += 1
                question = row['Question']
                correct_answer = row['Correct Answer']  # Full correct answer from CSV
                user_answer = selected_answers.get(question)
                first_char = user_answer[0] if user_answer else None

                # Check if the first letter of the selected answer matches the correct answer's first letter
                if first_char == correct_answer[0]:
                    correct_answers += 1

                questions_data.append({
                    'question': question,
                    'choices': [row['Answer A'], row['Answer B'], row['Answer C'], row['Answer D']],
                    'correct_answer': correct_answer,  # Include full correct answer
                    'selected_answer': user_answer
                })

        # Calculate the score
        score = f'You got {correct_answers} out of {total_questions} correct!'
        return render_template('quiz_copy.html', questions=questions_data, score=score)

    # Load the quiz questions for the form
    questions = []
    with open(quiz_full_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            questions.append({
                'question': row['Question'],
                'choices': [row['Answer A'], row['Answer B'], row['Answer C'], row['Answer D']],
            })
    
    return render_template('public_quiz.html', questions=questions)





# Display copy of quiz after submitting answers
@app.route('/quiz_copy/<quiz_path>', methods=['GET'])
def quiz_copy(quiz_path):
    quiz_full_path = os.path.join('static/quizzes', quiz_path)

    # Load the quiz questions with correct answers
    questions = []
    with open(quiz_full_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            questions.append({
                'question': row['Question'],
                'choices': [row['Answer A'], row['Answer B'], row['Answer C'], row['Answer D']],
                'correct_answer': row['Correct Answer']  # Include correct answer from CSV
            })

    # Render the copy of the quiz with the correct answers
    return render_template('quiz_copy.html', questions=questions)





# PDF output route
@app.route('/pdf_output/<int:pdf_id>')
def pdf_output(pdf_id):
    pdf_data = PDFData.query.get_or_404(pdf_id)
    return render_template('pdf_output.html', extracted_text=pdf_data.extracted_text)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists. Please use a different email.', 'danger')
            return redirect(url_for('register'))

        # If the email does not exist, create a new user
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user:
            if user.password == password:  # Compare plain text passwords
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        user_id = request.form['user_id']
        if pdf_file and user_id:
            pdf_path = f'static/pdfs/{pdf_file.filename}'
            pdf_file.save(pdf_path)

            # Extract text from PDF and generate questions
            extracted_text = extract_text_from_pdf(pdf_path)
            questions_text = generate_questions(extracted_text)

            # Ensure the quizzes directory exists
            quizzes_dir = 'static/quizzes'
            if not os.path.exists(quizzes_dir):
                os.makedirs(quizzes_dir)

            # Save the questions to CSV
            csv_path = os.path.join(quizzes_dir, f'{user_id}_quiz.csv')
            save_questions_to_csv(questions_text, csv_path)

            # Create an assignment
            assignment = Assignment(pdf_path=pdf_path, quiz_path=csv_path, user_id=user_id)
            db.session.add(assignment)
            db.session.commit()

            flash('Assignment created successfully!', 'success')
            return redirect(url_for('admin'))

    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return render_template('admin_dashboard.html')  # Admin-specific dashboard
    else:
        assignments = Assignment.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', assignments=assignments)  # User-specific dashboard


@app.route('/take_test/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def take_test(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.assigned_user != current_user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Process the quiz submission
        selected_answers = request.form.to_dict()
        correct_answers = 0
        total_questions = 0

        questions = []  # List to store each question with the correct answer and user's selected answer

        with open(assignment.quiz_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                total_questions += 1
                question = row['Question']
                correct_answer = row['Correct Answer'][0]
                user_answer = selected_answers.get(question)
                first_char = user_answer[0] if user_answer else None

                # Check if the answer is correct
                if first_char == correct_answer:
                    correct_answers += 1

                # Store the question, correct answer, and selected answer
                questions.append({
                    'question': question,
                    'correct_answer': row['Correct Answer'],
                    'choices': [row['Answer A'], row['Answer B'], row['Answer C'], row['Answer D']],
                    'selected_answer': user_answer
                })

        # Store the selected_answers in the session for access in the results page
        session['selected_answers'] = selected_answers

        # Store the score in the session or pass it via URL
        score = f'You got {correct_answers} out of {total_questions} correct!'
        flash(score, 'success')

        # Redirect to the results page
        return redirect(url_for('logged_quiz_results', quiz_path=assignment.quiz_path, score=score))

    # Load the quiz questions for the test page
    questions = []
    with open(assignment.quiz_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            questions.append({
                'question': row['Question'],
                'choices': [row['Answer A'], row['Answer B'], row['Answer C'], row['Answer D']],
            })

    return render_template('take_test.html', questions=questions, assignment=assignment)


@app.route('/logged_quiz_results', methods=['GET'])
@login_required
def logged_quiz_results():
    # Get the score from the request arguments
    score = request.args.get('score')
    quiz_path = request.args.get('quiz_path')

    # Retrieve the selected_answers from the session
    selected_answers = session.get('selected_answers')

    questions = []
    with open(quiz_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            question_text = row['Question']
            correct_answer = row['Correct Answer']
            selected_answer = selected_answers.get(question_text)

            questions.append({
                'question': question_text,
                'correct_answer': correct_answer,
                'choices': [row['Answer A'], row['Answer B'], row['Answer C'], row['Answer D']],
                'selected_answer': selected_answer
            })

    return render_template('logged_quiz_results.html', questions=questions, score=score)




if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # This will create the tables if they do not exist

        # Manually create an admin user with plain text password
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', password='garrett', is_admin=True)
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
