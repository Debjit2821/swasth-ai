from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<User {self.name}>"
class Case(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    symptoms = db.Column(db.Text, nullable=False)

    ai_response = db.Column(db.Text, nullable=False)

    danger_level = db.Column(db.String(20), nullable=False)

    status = db.Column(db.String(50), default="Pending")
    

    created_at = db.Column(db.DateTime, server_default=db.func.now())