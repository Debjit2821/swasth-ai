

from flask import Flask, flash, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from models import db, User, Case, Report, Appointment, Notification
from flask_mail import (
    Mail,
    Message
)

from itsdangerous import (
    URLSafeTimedSerializer
)

from ai.symptom_analysis import (
    analyze_symptoms,
    detect_specialist,
    generate_case_summary
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from ai.report_summary import summarize_report
import os
import random


app = Flask(__name__)
oauth = OAuth(app)

google = oauth.register(

    name="google",

    client_id=os.getenv(
        "GOOGLE_CLIENT_ID"
    ),

    client_secret=os.getenv(
        "GOOGLE_CLIENT_SECRET"
    ),

    server_metadata_url=
    "https://accounts.google.com/.well-known/openid-configuration",

    client_kwargs={
        "scope": "openid email profile"
    }
)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'

app.config['MAIL_PORT'] = 587

app.config['MAIL_USE_TLS'] = True

app.config['MAIL_TIMEOUT'] = 10

app.config['MAIL_USERNAME'] = os.getenv(
    "MAIL_USERNAME"
)

app.config['MAIL_PASSWORD'] = os.getenv(
    "MAIL_PASSWORD"
)

mail = Mail(app)


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config[
    "SQLALCHEMY_ENGINE_OPTIONS"
] = {

    "pool_pre_ping": True,

    "pool_recycle": 300
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "fallback_secret_key_2026"
)

serializer = URLSafeTimedSerializer(
    str(app.config["SECRET_KEY"])
)
db.init_app(app)

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


with app.app_context():

    db.create_all()


# ROOT
@app.route("/")
def root():

    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = (
            request.form["email"]
            .lower()
            .strip()
)

        password = request.form["password"]

        role = request.form["role"]

        specialization = request.form.get(
            "specialization"
        )

        # CHECK EXISTING EMAIL

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "Email already registered.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        # CREATE USER

        new_user = User(

            name=name,

            email=email,

            password=generate_password_hash(
            password
            ),

            role=role,

            specialization=specialization
        )

        db.session.add(new_user)

        try:

            db.session.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Exception as e:

            db.session.rollback()

            print(e)

            flash(
                "Something went wrong during registration.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

    return render_template(
        "register.html"
    )
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            # SUPERVISOR APPROVAL

            if (
                user.role == "supervisor"
                and not user.approved
            ):

                flash(
                    "Account Pending Admin Approval",
                    "warning"
                )

                return redirect(
                    url_for("login")
                )

            login_user(user)

            role = user.role.strip().lower()

            if role == "admin":

                return redirect("/admin")

            elif role == "supervisor":

                return redirect("/supervisor")

            return redirect("/dashboard")

        flash(
            "Invalid Credentials",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "login.html"
    )
# DASHBOARD
# USER DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():

    user_cases = Case.query.filter_by(
        user_id=current_user.id
    ).all()

    reports = (
    Report.query
    .order_by(Report.id.desc())
    .limit(10)
    .all()
)

    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).all()

    supervisors = User.query.filter_by(
        role="supervisor"
    ).all()

    notifications =(
         Notification.query.filter_by(
        user_id=current_user.id
    )
    .order_by(Notification.id.desc())
    .limit(10)
    .all()
)

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

# HOME CHATBOT
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():

    result = ""

    symptoms = ""

    danger_level = "Low"

    user_cases = []

    # ACTIVE CASE

    active_case = (
        Case.query.filter_by(
            user_id=current_user.id,
            status="Pending"
        )
        .first()
    )

    current_stage = "collecting_symptoms"

    # CREATE CASE IF NONE EXISTS

    if not active_case:

        active_case = Case(

            user_id=current_user.id,

            symptoms="",

            status="Pending",

            conversation_stage="collecting_symptoms"
        )

        db.session.add(active_case)

        db.session.commit()

    if (
        active_case
        and active_case.conversation_stage
    ):

        current_stage = (
            active_case.conversation_stage
        )

    # POST REQUEST

    if request.method == "POST":

        symptoms = request.form.get(
            "symptoms",
            ""
        ).strip()

        if not symptoms:

            return redirect(
                url_for("home")
            )

        symptoms = symptoms[:300]
        # =========================================
    # SAVE USER MESSAGE
    # =========================================

        if not active_case.chat_history:
        
            active_case.chat_history = ""

        active_case.chat_history += (
            f"||USER|| {symptoms} ||END||"
        )
        active_case.symptoms += (
            "\n" + symptoms
        )

      # -----------------------------------
        # INPUT GUARDRAILS
        # -----------------------------------

        non_medical_keywords = [
        
            "hello",
            "hi",
            "hey",
            "bye",
            "good morning",
            "good night",
            "how are you",
            "thanks",
            "thank you",
            "ok",
            "okay"
        ]

        medical_keywords = [
        
            "pain",
            "fever",
            "headache",
            "cough",
            "cold",
            "vomit",
            "vomiting",
            "heart",
            "chest",
            "stress",
            "anxiety",
            "rash",
            "infection",
            "dizziness",
            "breathing",
            "skin",
            "nerve",
            "weakness",
            "migraine",
            "pressure",
            "burning",
            "fatigue",
            "seizure",
            "stroke",
            "itching",
            "acne",
            "numbness"
        ]

        # GREETING / NON MEDICAL CHAT

        if (
        
            symptoms.lower() in non_medical_keywords

            and current_stage not in [
            
                "asking_more_symptoms",
                "appointment_mode",
                "appointment_date",
                "appointment_time"
            ]
        ):

            result = (
                "Please describe your medical "
                "symptoms only so I can assist "
                "you properly."
            )

        # INVALID / RANDOM INPUT

        elif (
        
            current_stage in [
            
                "collecting_symptoms",
                "asking_more_symptoms"
            ]

            and symptoms.lower() not in [
            
                "yes",
                "no"
            ]

            and not any(
                word in symptoms.lower()
                for word in medical_keywords
            )
        ):

            result = (
                "This does not appear to be "
                "a valid medical symptom. "
                "Please describe your "
                "health issue clearly."
            )

        # TOO SHORT

        elif (
        
            current_stage in [
            
                "collecting_symptoms",
                "asking_more_symptoms"
            ]

            and symptoms.lower() not in [
            
                "yes",
                "no"
            ]

            and len(symptoms.split()) < 2
        ):

            result = (
                "Please provide more detailed "
                "medical symptoms."
            )
        # STAGE 1

        elif current_stage == "collecting_symptoms":

            conversation_context = symptoms

            if (
                active_case
                and active_case.symptoms
            ):

                conversation_context = (

                    active_case.symptoms[-500:]
                    + "\n"
                    + symptoms
                )

            result, specialist = (
                analyze_symptoms(
                    conversation_context
                )
            )

            result += (
                "\n\nDo you have any "
                "other symptoms? "
                "(yes/no)"
            )
            active_case.conversation_stage = (
                "asking_more_symptoms"
            )

        # STAGE 2

        elif current_stage == "asking_more_symptoms":

            if symptoms.lower() == "yes":

                result = (
                    "Please describe "
                    "your additional symptoms."
                )

            elif symptoms.lower() == "no":

                active_case.conversation_stage = (
                    "appointment_mode"
                )

                result = (
                    "Would you like "
                    "an Online or Offline "
                    "consultation?"
                )

            else:

                conversation_context = (

                    active_case.symptoms[-500:]
                    + "\n"
                    + symptoms
                )

                result, specialist = (
                    analyze_symptoms(
                        conversation_context
                    )
                )

                result += (
                    "\n\nDo you have any "
                    "other symptoms? "
                    "(yes/no)"
                )

        # STAGE 3

        elif current_stage == "appointment_mode":

            # VALIDATE CONSULTATION TYPE

            if symptoms.lower() not in [

                "online",
                "offline"
                ]:

                result = (
                 "Please choose either "
                "'Online' or 'Offline' "
                "consultation."
             )

            else:

                active_case.appointment_mode = (
                    symptoms.capitalize()
                )

                active_case.conversation_stage = (
                    "appointment_date"
                )

                result = (
                    "Please choose an appointment date:\n\n"

                    "1. today\n"
                    "2. tomorrow\n"
                    "3. day after tomorrow"
                )

# STAGE 4

        elif current_stage == "appointment_date":

            valid_dates = [
            
                "today",
                "tomorrow",
                "day after tomorrow"
            ]

    # INVALID DATE

            if symptoms.lower() not in valid_dates:
            
                result = (
                    "Please choose a valid date:\n\n"

                    "1. today\n"
                    "2. tomorrow\n"
                    "3. day after tomorrow"
                )

            else:

                active_case.appointment_selected_date = (
                    symptoms.title()
                )

                active_case.conversation_stage = (
                    "appointment_time"
                )

                result = (
                    "Please choose a time slot:\n\n"

                    "1. 10am\n"
                    "2. 12pm\n"
                    "3. 3pm\n"
                    "4. 6pm"
                )
        # STAGE 5

        elif current_stage == "appointment_time":

            valid_slots = {

                "10am": "10:00 AM",

                "12pm": "12:00 PM",

                "3pm": "3:00 PM",

                "6pm": "6:00 PM"
            }

            # INVALID SLOT

            if symptoms.lower() not in valid_slots:

                result = (
                    "Please choose a valid "
                    "time slot.\n\n"

                    "Available slots:\n"
                    "10am\n"
                    "12pm\n"
                    "3pm\n"
                    "6pm"
                )

            else:

                appointment_time = (
                    valid_slots[
                        symptoms.lower()
                    ]
                )

                specialist = (
                    detect_specialist(
                        active_case.symptoms
                    )
                )

                # FIND DOCTOR

                doctor = (
                    User.query.filter_by(
                        role="supervisor",
                        specialization=specialist,
                        approved=True
                    )
                    .first()
                )

                # FALLBACK

                if not doctor:

                    doctor = (
                        User.query.filter_by(
                            role="supervisor",
                            approved=True
                        )
                        .first()
                    )

                # CHECK SLOT AVAILABILITY

                existing_slot = Appointment.query.filter_by(

                    supervisor_id=doctor.id,

                    appointment_date=(
                        active_case.appointment_selected_date
                    ),

                    appointment_time=appointment_time,

                    status="Scheduled"

                ).first()

                # SLOT ALREADY BOOKED

                if existing_slot:

                    result = (
                        f"Sorry, Dr. {doctor.name} "
                        f"already has an appointment "
                        f"on {active_case.appointment_selected_date} "
                        f"at {appointment_time}.\n\n"

                        "Please choose another slot."
                    )

                else:

                    # CREATE APPOINTMENT

                    appointment = Appointment(

                        patient_id=current_user.id,

                        supervisor_id=doctor.id,

                        case_id=active_case.id,

                        appointment_date=(
                            active_case
                            .appointment_selected_date
                        ),

                        appointment_time=(
                            appointment_time
                        ),

                        status="Scheduled"
                    )

                    db.session.add(
                        appointment
                    )

                    # CREATE NOTIFICATION

                    notification = Notification(

                        user_id=current_user.id,

                        message=(
                            f"Appointment with "
                            f"Dr. {doctor.name} "
                            f"scheduled."
                        )
                    )

                    db.session.add(
                        notification
                    )

                    # GENERATE SUMMARY

                    active_case.ai_summary = (
                        generate_case_summary(
                            active_case.symptoms[-500:]
                        )
                    )

                    # SUCCESS RESPONSE

                    result = f"""
        Appointment Confirmed ✅

        Doctor:
        Dr. {doctor.name}

        Specialization:
        {doctor.specialization}

        Date:
        {active_case.appointment_selected_date}

        Time:
        {appointment_time}
        """

                    active_case.conversation_stage = (
                        "appointment_confirmed"
                    )
    user_cases = (
        Case.query.filter_by(
            user_id=current_user.id
        )
        .order_by(
            Case.id.desc()
        )
        .limit(10)
        .all()
    )
    # =========================================
# SAVE AI RESPONSE
# =========================================

    if result:
        if not active_case.chat_history:

            active_case.chat_history = ""
        active_case.chat_history += (
            f"||AI|| {result} ||END||"
        )
    db.session.commit()
    return render_template(
            
            "index.html",

            result=result,

            symptoms=symptoms,

            user_cases=user_cases,

            active_case=active_case
        )
      
@app.route("/supervisor")
@login_required
def supervisor_dashboard():

    if current_user.role != "supervisor":

        flash("Access denied.")

        return redirect(url_for("dashboard"))

    appointments = Appointment.query.filter_by(
        supervisor_id=current_user.id
    ).all()

    cases = Case.query.all()

    return render_template(
        "supervisor.html",
        appointments=appointments,
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

    # GET RELATED CASE

    related_case = Case.query.get(
        appointment.case_id
    )

    # START FOLLOW-UP FLOW

    related_case.conversation_stage = "follow_up"

    # NOTIFICATION

    notification = Notification(
        user_id=appointment.patient_id,
        message="""
Your doctor submitted a medical report.

Please complete AI follow-up analysis
before closing consultation.
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

    # SECURITY CHECK

    if current_user.role != "supervisor":

        flash(
            "Access Denied",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    
    # RELATED CASE

    related_case = Case.query.get(
        appointment.case_id
    )

    if request.method == "POST":

        diagnosis = request.form[
            "diagnosis"
        ]

        prescription = request.form[
            "prescription"
        ]

        advice = request.form[
            "advice"
        ]

        # CREATE REPORT

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

        # NOTIFICATION

        notification = Notification(

            user_id=appointment.patient_id,

            message="""
Your doctor has added a new medical report.
"""
        )

        db.session.add(notification)

        # START FOLLOW-UP FLOW

        related_case.conversation_stage = (
            "follow_up"
        )

        db.session.commit()

        flash(
            "Report uploaded successfully.",
            "success"
        )

        return redirect(
            url_for(
                "supervisor_dashboard"
            )
        )

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
# REPORT FOLLOW-UP
@app.route("/report-followup/<int:case_id>", methods=["POST"])
@login_required
def report_followup(case_id):

    case = Case.query.get(case_id)

    current_update = request.form["followup"]

    context = f"""
Previous Symptoms:
{case.symptoms}

Doctor Summary:
{case.ai_summary}

Current Patient Condition:
{current_update}
"""

    result, specialist = analyze_symptoms(
        context
    )

    # SAVE FOLLOW-UP

    case.chat_history += f"""

FOLLOW-UP UPDATE:
{current_update}

AI FOLLOW-UP:
{result}

"""

    db.session.commit()

    return render_template(
        "followup_result.html",
        result=result,
        case=case
    )

# LOGOUT
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/login")

    # ONLY SUPERVISOR

    if current_user.role != "supervisor":

        flash(
            "Access Denied",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        entered_otp = request.form["otp"]

        if entered_otp == appointment.meeting_otp:

            appointment.otp_verified = True

            db.session.commit()

            flash(
                "Meeting Verified Successfully",
                "success"
            )

            return redirect(
                url_for(
                    "supervisor_dashboard"
                )
            )

        else:

            flash(
                "Invalid OTP",
                "danger"
            )

    return render_template(
        "verify_otp.html",
        appointment=appointment
    )
# FORGOT PASSWORD
@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user:

            token = serializer.dumps(
                email,
                salt="password-reset"
            )

            reset_link = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            msg = Message(

                "SWASTH-AI Password Reset",

                sender=app.config[
                    'MAIL_USERNAME'
                ],

                recipients=[email]
            )

            msg.body = f"""
Click the link below to reset your password:

{reset_link}

This link expires in 30 minutes.
"""

            try:

                mail.send(msg)

                flash(
                   "Password reset email sent.",
                    "success"
                    )

            except Exception as e:

                print(e)

                flash(
                    "Email sending failed.",
                    "danger"
                )

        else:

            flash(
                "Email not found.",
                "danger"
            )

    return render_template(
        "forgot_password.html"
    )
# RESET PASSWORD
@app.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    try:

        email = serializer.loads(

            token,

            salt="password-reset",

            max_age=1800
        )

    except Exception:

        flash(
            "Reset link expired or invalid.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    user = User.query.filter_by(
        email=email
    ).first()

    if request.method == "POST":

        new_password = request.form[
            "password"
        ]

        user.password = (
            generate_password_hash(
                new_password
            )
        )

        db.session.commit()

        flash(
            "Password updated successfully.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "reset_password.html"
    )
# GOOGLE LOGIN
@app.route("/google-login")
def google_login():

    redirect_uri = url_for(
        "google_authorized",
        _external=True
    )

    return google.authorize_redirect(
        redirect_uri
    )
# GOOGLE AUTHORIZED
@app.route("/google-authorized")
def google_authorized():

    token = google.authorize_access_token()
    if not token:

        flash(
            "Google login failed.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    user_info = token.get(
        "userinfo"
    )

    email = user_info["email"]

    name = user_info.get(
        "name",
        "Google User"
    )

    # CHECK EXISTING USER

    user = User.query.filter_by(
        email=email
    ).first()

    # CREATE NEW USER

    if not user:

        user = User(

            name=name,

            email=email,

            password=generate_password_hash(
                "google-auth-user"
            ),

            role="user",

            approved=True,

            specialization=None
        )

        db.session.add(user)

        db.session.commit()

    login_user(user)

    return redirect("/dashboard")
if __name__ == "__main__":

    app.run(debug=True)