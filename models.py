from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# USER MODEL
class User(UserMixin, db.Model):

    cases = db.relationship(
    'Case',
    backref='patient',
    lazy=True
)

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), nullable=False)

    approved = db.Column(db.Boolean, default=False)

    specialization = db.Column(db.String(100))

    def __repr__(self):

        return f"<User {self.name}>"


class Case(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    symptoms = db.Column(
        db.Text,
        nullable=False
    )

    ai_response = db.Column(
        db.Text,
        nullable=False
    )

    ai_summary = db.Column(
        db.Text
    )

    danger_level = db.Column(
        db.String(50),
        default="Low"
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    conversation_stage = db.Column(
        db.String(50),
        default="collecting_symptoms"
    )

    chat_history = db.Column(
        db.Text
    )

    appointment_selected_date = db.Column(
        db.String(100)
    )

    appointment_mode = db.Column(
        db.String(50)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

# REPORT MODEL
class Report(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    case_id = db.Column(
        db.Integer,
        db.ForeignKey('case.id'),
        nullable=False
    )

    doctor_notes = db.Column(db.Text, nullable=False)

    medicine_schedule = db.Column(db.Text, nullable=False)

    ai_summary = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
# APPOINTMENT MODEL
class Appointment(db.Model):

    meeting_otp = db.Column(
    db.String(10)
)

    otp_verified = db.Column(
    db.Boolean,
    default=False
)

    case_id = db.Column(
    db.Integer,
    db.ForeignKey('case.id')
)

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    supervisor_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    appointment_date = db.Column(
        db.String(100),
        nullable=False
    )

    appointment_time = db.Column(db.String(50))

    status = db.Column(
        db.String(50),
        default="Scheduled"
    )
# NOTIFICATIONS

class Notification(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )