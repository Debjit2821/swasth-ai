from flask import Flask, render_template, request
from models import db, User, Case
from ai.symptom_analysis import analyze_symptoms

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:deyken2821b@localhost:5432/swasthai'

app.config['SECRET_KEY'] = 'secretkey'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def home():

    result = ""

    if request.method == "POST":

        symptoms = request.form["symptoms"]

        # AI Analysis
        result = analyze_symptoms(symptoms)

        # Danger Detection
        danger_level = "Low"

        if "high" in result.lower():
            danger_level = "High"

        elif "medium" in result.lower():
            danger_level = "Medium"

        # Save Case in Database
        new_case = Case(
            symptoms=symptoms,
            ai_response=result,
            danger_level=danger_level
        )

        db.session.add(new_case)

        db.session.commit()

    return render_template(
        "index.html",
        result=result
    )

if __name__ == "__main__":
    app.run(debug=True)