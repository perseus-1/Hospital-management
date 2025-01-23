from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from fpdf import FPDF
from flask_mail import Mail, Message
from dotenv import load_dotenv
import base64
from flask_cors import CORS

load_dotenv()


app = Flask(__name__)
CORS(app)

app.secret_key = "OKgMirvqTJ3Yqis4c3xAujg0xJMlvlMFsW3HTtoi9AU"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL") or 'sqlite:///hospital.db'
db = SQLAlchemy(app)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  #SMTP server
app.config['MAIL_PORT'] = 587  #SMTP port
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] =  os.environ.get('MAIL_USERNAME')#email address
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  #App Password
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') # email address used to send email
mail = Mail(app)
    
# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_username = db.Column(db.String(50), nullable=False)
    day = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(10), nullable=False)
    patient_username = db.Column(db.String(50), nullable=True)
    
    def __repr__(self):
            return f"<Appointment doctor:{self.doctor_username},date:{self.day},time:{self.time_slot},user:{self.patient_username}>"

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('records', lazy=True))


class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(300), nullable = False)
    patient_username = db.Column(db.String(50), nullable = False)
    
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref=db.backref('prescriptions', lazy=True))

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.String(50), unique=True, nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# Specify the folder to store uploaded medical records
UPLOAD_FOLDER = 'static/uploads'
PRESCRIPTION_FOLDER = 'static/prescriptions'  # New Folder for prescriptions
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PRESCRIPTION_FOLDER'] = PRESCRIPTION_FOLDER  # Add the new folder config


# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(PRESCRIPTION_FOLDER):  # Ensure the prescriptions folder exists
    os.makedirs(PRESCRIPTION_FOLDER)

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            if user.role == 'patient':
                return redirect(url_for('home_patient'))
            elif user.role == 'doctor':
                return redirect(url_for('home_doctor'))
            elif user.role == 'pharmacist':
                return redirect(url_for('home_pharmacist'))
            elif user.role == 'receptionist':
                return redirect(url_for('home_receptionist'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')  # Fix here
        role = request.form['role']
        
        new_user = User(username=username, name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/upload_records', methods=['GET', 'POST'])
def upload_records():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Store the record in the database with the user's id
            new_record = Record(filename=filename, user_id=session['user_id'])
            db.session.add(new_record)
            db.session.commit()

            flash('Medical record uploaded successfully!')
            return redirect(url_for('view_records'))
    return render_template('upload_records.html')


@app.route('/access_records', methods=['GET', 'POST'])
def access_records():
    if request.method == 'POST':
        patient_username = request.form.get('patient_username')
        patient = User.query.filter_by(username=patient_username).first()
        
        if patient:
            records = Record.query.filter_by(user_id=patient.id).all()
            filenames = [record.filename for record in records]
            return render_template('access_records.html', records=filenames, patient_username=patient_username)
        else:
           flash("Invalid patient username","danger")
    return render_template('access_records.html')


@app.route('/view_records', methods = ['GET'])
def view_records():
    user_role = session.get('role')
    user_id = session.get('user_id')
    is_doctor_view = request.args.get('is_doctor_view')
    if is_doctor_view == 'True':
        records = Record.query.all()
        filenames = [record.filename for record in records]
        return render_template('view_records.html', records=filenames, is_doctor_view=True)
    elif user_role == 'patient':
        # Retrieve records only for the logged-in patient
        records = Record.query.filter_by(user_id=user_id).all()
        filenames = [record.filename for record in records]
        return render_template('view_records.html', records=filenames)
    elif user_role == 'doctor':
         records = Record.query.all()
         filenames = [record.filename for record in records]
         return render_template('view_records.html', records=filenames, is_doctor_view = True)
    else:
       filenames = []  
    return render_template('view_records.html', records=filenames)


@app.route('/upload_prescription', methods=['GET', 'POST'])
def upload_prescription():
     if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        patient_username = request.form.get('patient_username')
        if not patient_username:
            flash("please enter a valid patient username", "danger")
            return render_template('upload_prescription.html')
            
        patient = User.query.filter_by(username = patient_username).first()
        if not patient or patient.role != 'patient':
             flash("please enter a valid patient username", "danger")
             return render_template('upload_prescription.html')
             
        if file:
            filename = secure_filename(file.filename)
            
            # Create patient-specific directory if it doesn't exist
            patient_dir = os.path.join(app.config['PRESCRIPTION_FOLDER'], patient_username)
            os.makedirs(patient_dir, exist_ok=True)
            
            file_path = os.path.join(patient_dir, filename)
            file.save(file_path)
            
            # Store the prescription in the database with the user's id
            new_prescription = Prescription(filename=filename, doctor_id=session['user_id'], file_path = file_path, patient_username=patient_username)
            db.session.add(new_prescription)
            db.session.commit()

            flash('Prescription uploaded successfully!')
            return redirect(url_for('home_doctor')) # Redirect back to doctor home

     return render_template('upload_prescription.html')


@app.route('/view_prescription/<int:prescription_id>')
def view_prescription(prescription_id):
     prescription = Prescription.query.get_or_404(prescription_id)
     if os.path.exists(prescription.file_path):
            return send_file(prescription.file_path, as_attachment=True)
     else:
         flash("prescription file not found", "danger")
         return redirect(url_for('home_doctor'))


@app.route('/view_prescriptions', methods = ['GET', 'POST'])
def view_prescriptions():
    if request.method == 'POST':
        patient_username = request.form.get('patient_username')
        patient = User.query.filter_by(username=patient_username).first()
        
        if patient:
            prescriptions = Prescription.query.filter_by(patient_username=patient_username).all()
            return render_template('view_prescriptions.html', prescriptions=prescriptions, patient_username = patient_username)
        else:
            flash("Please enter a valid patient username","danger")
    return render_template('view_prescriptions.html')


@app.route('/view_appointments', methods = ['GET','POST'])
def view_appointments():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        today = datetime.now().date()
       
        if user_type == 'patient':
            appointments = Appointment.query.filter_by(patient_username=username).all()
            return render_template('view_appointments.html', appointments = appointments, username = username, user_type = user_type)
        elif user_type == 'doctor':
            doctor_username = username
            
            if request.method == 'POST':
                 selected_date_str = request.form.get('date')
                 if selected_date_str:
                     selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                 else:
                     selected_date = today
            else:
               selected_date = today

            dates = [today + timedelta(days=i) for i in range(7)]
            time_slots = ["9:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30", "16:30", "17:30", "18:30", "19:30", "20:30"]
    
            # Fetch all appointments for the doctor on selected date
            booked_appointments = Appointment.query.filter_by(doctor_username=doctor_username, day=selected_date).all()

            # Create a set of booked time slots for easy lookup
            booked_slots = {(app.time_slot, app.day) for app in booked_appointments}

            return render_template('view_appointments.html', dates=dates, time_slots=time_slots, selected_date=selected_date, booked_slots = booked_slots, user_type = user_type, username = username, appointments = booked_appointments)
        else:
             flash("Select either patient or doctor", "danger")
             return render_template('view_appointments.html')

    return render_template('view_appointments.html')


@app.route('/view_schedule', methods=['GET', 'POST'])
def view_schedule():
    doctor_username = session.get('username')
    today = datetime.now().date()
    
    if request.method == 'POST':
        selected_date_str = request.form.get('date')
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
          selected_date = today

    dates = [today + timedelta(days=i) for i in range(7)]
    time_slots = ["9:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30", "16:30", "17:30", "18:30", "19:30", "20:30"]
    
    # Fetch all appointments for the doctor on selected date
    booked_appointments = Appointment.query.filter_by(doctor_username=doctor_username, day=selected_date).all()

    # Create a set of booked time slots for easy lookup
    booked_slots = {(app.time_slot, app.day) for app in booked_appointments}

    return render_template('view_schedule.html', dates=dates, time_slots=time_slots, selected_date=selected_date, booked_slots = booked_slots)


@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    doctors = User.query.filter_by(role='doctor').all()
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(1, 8)]
    time_slots = ["9:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30", "16:30", "17:30", "18:30", "19:30", "20:30"]
    selected_date = today
     # Fetch all appointments for the given date
    all_appointments = Appointment.query.filter(Appointment.day >= today).all()
    booked_slots = {(app.time_slot, app.day) for app in all_appointments}
    
    if request.method == 'POST':
        selected_doctor = request.form.get('doctor')
        selected_date_str = request.form.get('date')
        selected_time = request.form.get('time')
        if not selected_date_str or not selected_time or not selected_doctor:
            return render_template('book_appointments.html', doctors=doctors, dates=dates, time_slots=time_slots, now=datetime.now(), booked_slots = booked_slots, selected_date = selected_date)

        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

        if selected_date not in dates:
            flash("Invalid date selected. Please select a date within the next 7 days.", "danger")
            return redirect(url_for('book_appointment'))
        if 'check_availability' not in request.form:
            existing_appointment = Appointment.query.filter_by(
                doctor_username=selected_doctor,
                day=selected_date,
                time_slot=selected_time
             ).first()

            if existing_appointment:
                flash("This time slot is already booked. Please choose another slot.", "danger")
                return render_template('book_appointments.html', doctors=doctors, dates=dates, time_slots=time_slots, now=datetime.now(), booked_slots = booked_slots, selected_date=selected_date)
    
            new_appointment = Appointment(
                doctor_username=selected_doctor,
                day=selected_date,
                time_slot=selected_time,
                patient_username=session['username']
            )
            db.session.add(new_appointment)
            db.session.commit()
            flash("Appointment booked successfully!", "success")
            return redirect(url_for('home_patient'))
    return render_template('book_appointments.html', doctors=doctors, dates=dates, time_slots=time_slots, now=datetime.now(), booked_slots = booked_slots, selected_date = selected_date)


@app.route('/home/doctor')
def home_doctor():
    doctor_username = session.get('username')
    today = datetime.now().date()
    appointments = Appointment.query.filter(Appointment.doctor_username == doctor_username, Appointment.day >= today).all()
    return render_template('home_doctor.html',appointments=appointments)

@app.route('/home/pharmacist')
def home_pharmacist():
     user = session.get('username')
     prescriptions = Prescription.query.all()
     return render_template('home_pharmacist.html',prescriptions = prescriptions)

@app.route('/home/receptionist')
def home_receptionist():
    today = datetime.now().date()
    appointments = Appointment.query.filter(Appointment.day >= today).all()
    return render_template('home_receptionist.html',appointments = appointments)

@app.route('/home/patient')
def home_patient():
    user = session['username']
    today = datetime.now().date()
    appointments = Appointment.query.filter(Appointment.patient_username == user, Appointment.day >= today).all()
    return render_template('home_patient.html',appointments=appointments)

@app.route('/view_medicine_stock', methods = ['GET'])
def view_medicine_stock():
     medicines = Medicine.query.all()
     return render_template('view_medicine_stock.html', medicines = medicines)

@app.route('/update_medicine_stock', methods=['GET','POST'])
def update_medicine_stock():
    if request.method == 'POST':
       medicine_id = request.form.get('medicine_id')
       action = request.form.get('action')
       quantity = request.form.get('quantity', type = int)
       
       medicine = Medicine.query.filter_by(medicine_id = medicine_id).first()
       if medicine:
           if action == 'add':
                medicine.quantity += quantity
           elif action == 'remove':
                if medicine.quantity >= quantity:
                  medicine.quantity -= quantity
                else:
                    flash("Not enough stock", "danger")
                    return render_template('update_medicine_stock.html', medicines = Medicine.query.all())
           db.session.commit()
           flash("medicine updated successfully","success")
           return redirect(url_for('view_medicine_stock'))
       else:
            flash("medicine does not exist", "danger")
       return render_template('update_medicine_stock.html', medicines = Medicine.query.all())

@app.route('/update_records', methods = ['GET', 'POST'])
def update_records():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        patient_username = request.form.get('patient_username')
        if not patient_username:
            flash("please enter a valid patient username", "danger")
            return render_template('update_records.html')
        
        patient = User.query.filter_by(username = patient_username).first()
        if not patient or patient.role != 'patient':
           flash("please enter a valid patient username","danger")
           return render_template('update_records.html')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_record = Record(filename=filename, user_id=patient.id)
            db.session.add(new_record)
            db.session.commit()
            flash('Medical record updated successfully!', 'success')
            return redirect(url_for('view_records'))
        return render_template('update_records.html')

@app.route('/pink_slip', methods = ['GET', 'POST'])
def pink_slip():
    if request.method == 'POST':
        patient_username = request.form.get('patient_username')
        patient = User.query.filter_by(username=patient_username).first()
        if not patient:
             flash('Invalid Username', "danger")
             return render_template('pink_slip.html')
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Pink Slip", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Patient ID: {patient.username}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Patient Name: {patient.name}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Date of Visit: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='L')

        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"pink_slip_{patient.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        pdf.output(pdf_path)
        
        msg = Message('Your Pink Slip', recipients=[patient.email])
        with app.open_resource(pdf_path) as fp:
            msg.attach(pdf_path, "application/pdf", fp.read())
        mail.send(msg)
        os.remove(pdf_path)
        flash('Pink slip generated and sent to email!', 'success')
        return redirect(url_for('home_receptionist'))
    return render_template('pink_slip.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)