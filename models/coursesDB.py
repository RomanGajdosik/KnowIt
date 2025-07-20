from app import db
from datetime import datetime

# Junction table for student course enrollments
student_enrollments = db.Table('student_enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('enrolled_at', db.DateTime, default=lambda: datetime.utcnow()),
    db.Column('status', db.String(20), default='enrolled')  # enrolled, completed, dropped
)

class Courses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by_user = db.relationship('Users', foreign_keys=[created_by], backref='courses_created')
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_user = db.relationship('Users', foreign_keys=[updated_by], backref='courses_updated')
    
    # Many-to-many relationship with students
    enrolled_students = db.relationship('Users', secondary=student_enrollments, backref='enrolled_courses')
    
    
