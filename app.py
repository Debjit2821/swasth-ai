from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from models import db, User, Case, Report, Appointment, Notification

from ai.symptom_analysis import (
    analyze_symptoms,
    detect_specialist,
    generate_case_summary
)
from ai.report_summary import summarize_report
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

db.init_app(app)

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


with app.app_context():

    db.create_all()


# ROOT
@app.route("/")
def root():

    return redirect("/login")


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        role = request.form["role"]

        specialization = request.form["specialization"]

        approved = False

        # NORMAL USERS AUTO APPROVED
        if role == "user":

            approved = True

        new_user = User(
            name=name,
            email=email,
            password=password,
            role=role,
            approved=approved,
            specialization=specialization
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        if user:

            if not user.approved:

                return "Account Pending Admin Approval"

            login_user(user)

            role = user.role.strip().lower()

            if role == "admin":

                return redirect("/admin")

            elif role == "supervisor":

                return redirect("/supervisor")

            return redirect("/dashboard")

        return "Invalid Credentials"

    return render_template("login.html")


# DASHBOARD
# USER DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():

    user_cases = Case.query.filter_by(
        user_id=current_user.id
    ).all()

    reports = Report.query.all()

    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).all()

    supervisors = User.query.filter_by(
        role="supervisor"
    ).all()

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "dashboard.html",
        user_cases=user_cases,
        reports=reports,
        appointments=appointments,
        supervisors=supervisors,
        notifications=notifications
    )
# CLOSE CONSULTATION
@app.route("/close-consultation/<int:case_id>")
@login_required
def close_consultation(case_id):

    case = Case.query.get(case_id)

    if case.user_id == current_user.id:

        case.status = "Resolved"

        db.session.commit()

    return redirect("/dashboard")
# CASE TIMELINE
@app.route("/case-timeline/<int:case_id>")
@login_required
def case_timeline(case_id):

    case = Case.query.get(case_id)

    reports = Report.query.filter_by(
        case_id=case.id
    ).all()

    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).all()

    supervisors = User.query.filter_by(
        role="supervisor"
    ).all()

    return render_template(
        "case_timeline.html",
        case=case,
        reports=reports,
        appointments=appointments,
        supervisors=supervisors
    )
# BOOK APPOINTMENT
@app.route("/book-appointment", methods=["GET", "POST"])
@login_required
def book_appointment():

    supervisors = User.query.filter_by(
        role="supervisor",
        approved=True
    ).all()

    if request.method == "POST":

        supervisor_id = request.form["supervisor_id"]

        appointment_date = request.form["appointment_date"]

        new_appointment = Appointment(
            patient_id=current_user.id,
            supervisor_id=supervisor_id,
            appointment_date=appointment_date
        )

        db.session.add(new_appointment)

        db.session.commit()

        return "Appointment Booked Successfully"

    return render_template(
        "book_appointment.html",
        supervisors=supervisors
    )

# HOME CHATBOT
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():

    result = ""

    symptoms = ""

    specialist = "General Physician"

    danger_level = "Low"

    if request.method == "POST":

        symptoms = request.form["symptoms"].strip()

        # NON-MEDICAL FILTER

        non_medical_keywords = [
            "hello",
            "hi",
            "thanks",
            "thank you",
            "okay",
            "ok",
            "bye"
        ]

        if symptoms.lower() in non_medical_keywords:

            return render_template(
                "index.html",
                result="Please describe your medical symptoms so I can assist you.",
                danger_level=danger_level
            )

        # ACTIVE CASE

        active_case = Case.query.filter_by(
            user_id=current_user.id,
            status="Pending"
        ).first()

        # CURRENT STAGE

        current_stage = "collecting_symptoms"

        if active_case:

            current_stage = active_case.conversation_stage

        # -----------------------------------
        # STAGE 1 — COLLECT SYMPTOMS
        # -----------------------------------

        if current_stage == "collecting_symptoms":

            conversation_context = symptoms

            if active_case and active_case.symptoms:

                conversation_context = (
                    active_case.symptoms + "\n" + symptoms
                )

            result, specialist = analyze_symptoms(
                conversation_context
            )

            result += "\n\nDo you have any other symptoms? (yes/no)"

        # -----------------------------------
        # STAGE 2 — MORE SYMPTOMS
        # -----------------------------------

        elif current_stage == "asking_more_symptoms":

            if symptoms.lower() == "no":

                active_case.conversation_stage = "appointment_mode"

                result = """
Would you like an Online or Offline consultation?
"""

            else:

                conversation_context = (
                    active_case.symptoms + "\n" + symptoms
                )

                result, specialist = analyze_symptoms(
                    conversation_context
                )

                result += "\n\nAny other symptoms? (yes/no)"

        # -----------------------------------
        # STAGE 3 — APPOINTMENT MODE
        # -----------------------------------

        elif current_stage == "appointment_mode":

            active_case.appointment_mode = symptoms

            active_case.conversation_stage = "appointment_date"

            result = """
Great.

Please enter your preferred appointment date.

Example:
25 May 2026
"""

        # -----------------------------------
        # STAGE 4 — APPOINTMENT DATE
        # -----------------------------------

        elif current_stage == "appointment_date":

            active_case.appointment_selected_date = symptoms

            active_case.conversation_stage = "appointment_time"

            result = """
Please enter your preferred appointment time.

Example:
6:00 PM
"""

        # -----------------------------------
        # STAGE 5 — APPOINTMENT TIME
        # -----------------------------------

        elif current_stage == "appointment_time":

            appointment_time = symptoms

            specialist = "General Physician"

            if "Cardiologist" in active_case.ai_response:

                specialist = "Cardiologist"

            elif "Dermatologist" in active_case.ai_response:

                specialist = "Dermatologist"

            elif "Psychiatrist" in active_case.ai_response:

                specialist = "Psychiatrist"

            elif "Neurologist" in active_case.ai_response:

                specialist = "Neurologist"

            # FIND DOCTOR

            doctor = User.query.filter_by(
                role="supervisor",
                specialization=specialist,
                approved=True
            ).first()

            # FALLBACK

            if not doctor:

                doctor = User.query.filter_by(
                    role="supervisor",
                    specialization="General Physician",
                    approved=True
                ).first()

            # CHECK DUPLICATE APPOINTMENT

            existing_appointment = Appointment.query.filter_by(
                patient_id=current_user.id,
                status="Scheduled"
            ).first()

            if not existing_appointment and doctor:

                appointment = Appointment(
                    patient_id=current_user.id,
                    supervisor_id=doctor.id,
                    case_id=active_case.id,
                    appointment_date=active_case.appointment_selected_date,
                    appointment_time=appointment_time,
                    status="Scheduled"
                )

                db.session.add(appointment)

                # NOTIFICATION

                notification = Notification(
                    user_id=current_user.id,
                    message=f"""
Appointment scheduled with
Dr. {doctor.name}
on {active_case.appointment_selected_date}
at {appointment_time}.
"""
                )

                db.session.add(notification)

                result = f"""
Appointment Confirmed ✅

Doctor:
Dr. {doctor.name}

Specialization:
{doctor.specialization}

Mode:
{active_case.appointment_mode}

Date:
{active_case.appointment_selected_date}

Time:
{appointment_time}

Status:
Scheduled
"""

                active_case.conversation_stage = "appointment_confirmed"

            else:

                result = """
You already have an active scheduled appointment.
"""

        # -----------------------------------
        # DANGER DETECTION
        # -----------------------------------

        high_keywords = [
            "heart attack",
            "stroke",
            "breathing difficulty",
            "chest pain",
            "unconscious",
            "critical"
        ]

        medium_keywords = [
            "fever",
            "infection",
            "vomiting",
            "pain",
            "dizziness"
        ]

        for word in high_keywords:

            if word in result.lower():

                danger_level = "High"

        for word in medium_keywords:

            if word in result.lower() and danger_level != "High":

                danger_level = "Medium"

        # -----------------------------------
        # WORKFLOW WORDS
        # -----------------------------------

        workflow_words = [
            "yes",
            "no",
            "online",
            "offline"
        ]

        # -----------------------------------
        # UPDATE EXISTING CASE
        # -----------------------------------

        if active_case:

            if symptoms.lower() not in workflow_words:

                if active_case.symptoms:

                    active_case.symptoms += f"\n{symptoms}"

                else:

                    active_case.symptoms = symptoms

            active_case.ai_response = result

            active_case.ai_summary = generate_case_summary(
                active_case.symptoms
            )

            active_case.danger_level = danger_level

            # CHAT HISTORY

            if not active_case.chat_history:

                active_case.chat_history = ""

            active_case.chat_history += f"""

USER:
{symptoms}

AI:
{result}

"""

            # UPDATE STAGES

            if current_stage == "collecting_symptoms":

                active_case.conversation_stage = "asking_more_symptoms"

        # -----------------------------------
        # CREATE NEW CASE
        # -----------------------------------

        else:

            active_case = Case(
                symptoms=symptoms,
                ai_response=result,
                ai_summary=generate_case_summary(symptoms),
                chat_history=f"""

USER:
{symptoms}

AI:
{result}

""",
                danger_level=danger_level,
                user_id=current_user.id,
                conversation_stage="asking_more_symptoms"
            )

            db.session.add(active_case)

        # SAVE DATABASE

        db.session.commit()

    return render_template(
        "index.html",
        result=result,
        danger_level=danger_level
    )
# SUPERVISOR DASHBOARD
@app.route("/supervisor")
@login_required
def supervisor():

    if current_user.role != "supervisor":

        return "Access Denied"

    cases = Case.query.filter_by(
        status="Pending"
    ).all()

    return render_template(
        "supervisor.html",
        cases=cases
    )
# SUPERVISOR APPOINTMENTS
@app.route("/supervisor-appointments")
@login_required
def supervisor_appointments():

    appointments = Appointment.query.filter_by(
        supervisor_id=current_user.id
    ).all()

    patients = User.query.filter_by(
        role="user"
    ).all()

    return render_template(
        "supervisor_appointments.html",
        appointments=appointments,
        patients=patients
    )
# COMPLETE APPOINTMENT
@app.route("/complete-appointment/<int:appointment_id>")
@login_required
def complete_appointment(appointment_id):

    appointment = Appointment.query.get(
        appointment_id
    )

    appointment.status = "Completed"

    # NOTIFICATION

    notification = Notification(
        user_id=appointment.patient_id,
        message="""
Your consultation has been completed.
Please review your medical report.
"""
    )

    db.session.add(notification)

    db.session.commit()

    return redirect("/supervisor-appointments")
# ADD DOCTOR REPORT
@app.route(
    "/add-report/<int:appointment_id>",
    methods=["GET", "POST"]
)
@login_required
def add_report(appointment_id):

    appointment = Appointment.query.get(
        appointment_id
    )

    related_case = Case.query.get(
        appointment.case_id
    )

    if request.method == "POST":

        diagnosis = request.form["diagnosis"]

        prescription = request.form["prescription"]

        advice = request.form["advice"]

        report = Report(
            case_id=related_case.id,
            doctor_notes=f"""
Diagnosis:
{diagnosis}

Advice:
{advice}
""",
            medicine_schedule=prescription,
            ai_summary=related_case.ai_summary
        )

        db.session.add(report)
        # REPORT NOTIFICATION

        notification = Notification(
            user_id=appointment.patient_id,
            message="""
        Your doctor has added a new medical report.
        """
        )

        db.session.add(notification)

        db.session.commit()

        return redirect("/supervisor-appointments")

    return render_template(
        "add_report.html",
        appointment=appointment
    )
# ADMIN
@app.route("/admin")
@login_required
def admin_dashboard():

    if current_user.role != "admin":

        return "Access Denied"

    pending_supervisors = User.query.filter_by(
        role="supervisor",
        approved=False
    ).all()

    return render_template(
        "admin.html",
        pending_supervisors=pending_supervisors
    )


# APPROVE SUPERVISOR
@app.route("/approve-supervisor/<int:user_id>")
@login_required
def approve_supervisor(user_id):

    if current_user.role != "admin":

        return "Access Denied"

    user = User.query.get(user_id)

    user.approved = True

    db.session.commit()

    return redirect("/admin")


# UPDATE REPORT
@app.route("/update-report/<int:case_id>", methods=["GET", "POST"])
@login_required
def update_report(case_id):

    if request.method == "POST":

        doctor_notes = request.form["doctor_notes"]
        medicine_schedule = request.form["medicine_schedule"]

        ai_summary = summarize_report(doctor_notes)

        new_report = Report(
            case_id=case_id,
            doctor_notes=doctor_notes,
            medicine_schedule=medicine_schedule,
            ai_summary=ai_summary
        )

        db.session.add(new_report)
        db.session.commit()

        return "Report Submitted Successfully"

    return render_template("update_report.html")


# PATIENT REPORT
@app.route("/patient-report/<int:report_id>")
@login_required
def patient_report(report_id):

    report = Report.query.get(report_id)

    return render_template(
        "patient_report.html",
        report=report
    )


# FOLLOWUP
@app.route("/resolve-case/<int:case_id>", methods=["GET", "POST"])
@login_required
def resolve_case(case_id):

    case = Case.query.get(case_id)

    if request.method == "POST":

        recovery_response = request.form["recovery"]

        if recovery_response.lower() == "yes":

            case.status = "Resolved"

        else:

            case.status = "Follow-up Needed"

        db.session.commit()

        return f"Case Status Updated: {case.status}"

    return render_template(
        "resolve_case.html",
        case=case
    )
# VIEW REPORT
@app.route("/view-report/<int:report_id>")
@login_required
def view_report(report_id):

    report = Report.query.get(report_id)

    return render_template(
        "view_report.html",
        report=report
    )

# LOGOUT
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/login")


if __name__ == "__main__":

    app.run(debug=True)