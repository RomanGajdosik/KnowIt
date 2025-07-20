from flask import Flask, request, render_template,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user,UserMixin,current_user,login_required 
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.secret_key = os.getenv('SECRET_KEY')

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models.usersDB import Users
from models.coursesDB import Courses, student_enrollments


# Make Users model compatible with Flask-Login
class UserLogin(Users, UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated and current_user.role == 'student':
        # Show available courses for students
        courses = Courses.query.join(Users, Courses.created_by == Users.id)\
                              .filter(Users.role.in_(['teacher', 'admin']))\
                              .order_by(Courses.created_at.desc()).all()
        enrolled_course_ids = [course.id for course in current_user.enrolled_courses]
        return render_template('index.html', courses=courses, enrolled_course_ids=enrolled_course_ids, is_student=True)
    elif current_user.is_authenticated and current_user.role in ['teacher']:
        # Show courses created by the teacher
        courses = Courses.query.filter_by(created_by=current_user.id).order_by(Courses.created_at.desc()).all()
        return render_template('index.html', courses=courses, is_teacher=True)
    elif current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    show_modal = False
    if request.method == 'POST':
        fullName = request.form['fullName']
        username = request.form['username']
        email = request.form['email']
        phoneNumber = request.form['phone_number']
        password = request.form['password_hash']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        existing_user = Users.query.filter((Users.username == username) | (Users.email == email)).first()
        if existing_user:
            error = 'Username or email already exists. Please choose another.'
            show_modal = True
        else:
            new_user = Users(fullname=fullName, username=username, email=email,phone_number=phoneNumber, password_hash=hashed_password, created_at=db.func.current_timestamp())
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index', username=new_user.username))
    return render_template('register.html', error=error, show_modal=show_modal)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    show_modal = False
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password_hash']
        user = Users.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index' , username=username))
        else:
            error = 'Invalid username or password.'
            show_modal = True
    return render_template('login.html', error=error, show_modal=show_modal)

@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect('/')

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    users = Users.query.all()
    # Fetch contents for content management table
    try:
        contents = Courses.query.all()
    except Exception:
        contents = []
    return render_template('admin.html', users=users, contents=contents)

# Delete user route
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    user = Users.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin'))

# @app.route('/admin/delete-course/<int:course_id>', methods=['POST'])
# @login_required
# def delete_course(course_id):
#     if current_user.role != 'admin':
#         return redirect(url_for('index'))
#     course = Courses.query.get(course_id)
#     if course:
#         db.session.delete(course)
#         db.session.commit()
#     return redirect(url_for('admin'))


# Bulk role update for admin dashboard
@app.route('/admin/set_roles', methods=['POST'])
@login_required
def set_roles():
    if current_user.role != 'admin':
        return redirect(url_for('index'))    
    user_id = request.form.get('user_id')
    role = request.form.get('role')
    user = Users.query.get(user_id)
    print(f"Setting role for user {user_id} to {role}")
    if user:
        user.role = role
        db.session.commit()   
    print('here i am')
    return redirect(url_for('admin'))

@app.route('/add-content', methods=['GET', 'POST'])
@login_required
def add_content():
    # Only teachers and admins can create courses
    if current_user.role not in ['teacher', 'admin']:
        return redirect(url_for('index'))
    
    error = None
    message = None
    show_modal = False
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        content = request.form['content']
        
        # Check if course title already exists
        existing_course = Courses.query.filter_by(title=title).first()
        if existing_course:
            error = True
            message = 'A course with this title already exists. Please choose a different title.'
            show_modal = True
        else:
            try:
                new_course = Courses(
                    title=title,
                    description=description if description else None,
                    content=content,
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                db.session.add(new_course)
                db.session.commit()
                
                error = False
                message = f'Course "{title}" has been created successfully!'
                show_modal = True
            except Exception as e:
                error = True
                message = 'An error occurred while creating the course. Please try again.'
                show_modal = True
                db.session.rollback()
    
    return render_template('add_content.html', error=error, message=message, show_modal=show_modal)

@app.route('/my-courses')
@login_required
def my_courses():
    if current_user.role in ['teacher', 'admin']:
        # Teachers and admins see courses they created
        courses = Courses.query.filter_by(created_by=current_user.id).order_by(Courses.created_at.desc()).all()
        return render_template('my_courses.html', courses=courses)
    else:
        # Students see courses they're enrolled in
        enrolled_courses = current_user.enrolled_courses
        return render_template('my_courses.html', courses=enrolled_courses, is_student=True)

@app.route('/view-course/<int:course_id>')
@login_required
def view_course(course_id):
    course = Courses.query.get_or_404(course_id)
    
    # Check access permissions based on role
    if current_user.role in ['teacher', 'admin']:
        # Teachers/admins can view their own courses or (for admins) any course
        if course.created_by != current_user.id and current_user.role != 'admin':
            return redirect(url_for('my_courses'))
    else:
        # Students can only view courses they're enrolled in or browse available courses
        pass  # We'll handle this in the template
    
    # Check if student is enrolled (for students)
    is_enrolled = False
    if current_user.role == 'student':
        is_enrolled = course in current_user.enrolled_courses
    
    # Get enrolled students for teachers/admins
    enrolled_students = []
    if current_user.role in ['teacher', 'admin'] and (course.created_by == current_user.id or current_user.role == 'admin'):
        enrolled_students = course.enrolled_students
    
    return render_template('view_course.html', course=course, is_enrolled=is_enrolled, enrolled_students=enrolled_students)

@app.route('/edit-course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    # Only teachers and admins can edit courses
    if current_user.role not in ['teacher', 'admin']:
        return redirect(url_for('index'))
    
    course = Courses.query.get_or_404(course_id)
    # Check if user owns this course (or is admin)
    if course.created_by != current_user.id and current_user.role != 'admin':
        return redirect(url_for('my_courses'))
    
    error = None
    message = None
    show_modal = False
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        content = request.form['content']
        
        # Check if title already exists (excluding current course)
        existing_course = Courses.query.filter(Courses.title == title, Courses.id != course_id).first()
        if existing_course:
            error = True
            message = 'A course with this title already exists. Please choose a different title.'
            show_modal = True
        else:
            try:
                course.title = title
                course.description = description if description else None
                course.content = content
                course.updated_by = current_user.id
                db.session.commit()
                
                error = False
                message = f'Course "{title}" has been updated successfully!'
                show_modal = True
            except Exception as e:
                error = True
                message = 'An error occurred while updating the course. Please try again.'
                show_modal = True
                db.session.rollback()
    
    return render_template('edit_course.html', course=course, error=error, message=message, show_modal=show_modal)

@app.route('/delete-course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    # Only teachers and admins can delete courses
    if current_user.role not in ['teacher', 'admin']:
        return redirect(url_for('index'))
    
    course = Courses.query.get_or_404(course_id)
    # Check if user owns this course (or is admin)
    if course.created_by != current_user.id and current_user.role != 'admin':
        return redirect(url_for('my_courses'))
        
    try:
        db.session.delete(course)
        db.session.commit()
        message = f'Course "{course.title}" has been deleted successfully!'
        error = False
    except Exception as e:
        message = 'An error occurred while deleting the course. Please try again.'
        error = True
        db.session.rollback()
    
    if current_user.role == 'admin':
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('my_courses'))

# Route for students to browse all available courses
@app.route('/browse-courses')
@login_required
def browse_courses():
    # Show all courses created by teachers/admins
    courses = Courses.query.join(Users, Courses.created_by == Users.id)\
                          .filter(Users.role.in_(['teacher', 'admin']))\
                          .order_by(Courses.created_at.desc()).all()
    
    # Get user's enrolled courses to show enrollment status
    enrolled_course_ids = [course.id for course in current_user.enrolled_courses] if current_user.role == 'student' else []
    
    return render_template('browse_courses.html', courses=courses, enrolled_course_ids=enrolled_course_ids)

# Route for students to enroll in a course
@app.route('/enroll-course/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    if current_user.role != 'student':
        return redirect(url_for('index'))
    
    course = Courses.query.get_or_404(course_id)
    
    # Check if already enrolled
    if course not in current_user.enrolled_courses:
        current_user.enrolled_courses.append(course)
        db.session.commit()
    
    return redirect(url_for('browse_courses'))

# Route for students to unenroll from a course
@app.route('/unenroll-course/<int:course_id>', methods=['POST'])
@login_required
def unenroll_course(course_id):
    if current_user.role != 'student':
        return redirect(url_for('index'))
    
    course = Courses.query.get_or_404(course_id)
    
    # Check if enrolled and remove
    if course in current_user.enrolled_courses:
        current_user.enrolled_courses.remove(course)
        db.session.commit()
    
    return redirect(url_for('browse_courses'))

@app.route('/faq')
def faq():
    return render_template('faq.html')

if __name__ == '__main__':
    app.run()