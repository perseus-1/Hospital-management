#  Hospital Management System

A role-based web application built using **Flask**, **SQLite**, and **HTML/CSS** that streamlines hospital operations by enabling patients, doctors, pharmacists, and receptionists to interact via a unified digital platform.

---

##  Features

###  User Roles
- **Patient**: Book appointments, upload/view medical records, and receive prescriptions.
- **Doctor**: View schedule, access patient records, upload prescriptions.
- **Pharmacist**: View and manage prescription records and medicine stock.
- **Receptionist**: View all appointments, generate and send pink slips via email.

###  Appointment Booking
- Dynamic scheduling for doctors.
- Available time slots displayed in real-time.
- Validation to prevent double-booking.

###  Medical Record Management
- Patients can upload records.
- Doctors can view and update patient records.
- Role-based access control for security.

###  Prescription Management
- Doctors upload prescriptions tied to patient usernames.
- Pharmacists access all prescriptions for dispensing.
- Files stored in structured patient folders.

###  Medicine Stock System
- Pharmacists can add/remove medicines from inventory.
- Live view of all medicine quantities.

###  Pink Slip Generation
- Receptionists generate a PDF summary of visit details.
- Automatically sent to the patient’s registered email.
- Implemented with **FPDF** and **Flask-Mail**.

---

##  Tech Stack

| Frontend      | Backend     | Database     | Libraries/Tools            |
|---------------|-------------|--------------|-----------------------------|
| HTML, CSS     | Flask       | SQLite       | Flask-Mail, SQLAlchemy, FPDF, Flask-CORS, dotenv |

---

##  Screenshots

some screenshots

<img width="1896" height="902" alt="image" src="https://github.com/user-attachments/assets/82061e4d-3434-478a-ae53-2848d8c9b53c" />

<img width="1892" height="892" alt="image" src="https://github.com/user-attachments/assets/bd3ee10a-3709-4451-a11e-56df60b7e758" />



##  Setup Instructions

clone the repo

open cmd at the project directory and run with , python app.py



