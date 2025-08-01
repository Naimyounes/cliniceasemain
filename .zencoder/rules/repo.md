---
description: Repository Information Overview
alwaysApply: true
---

# ClinicEase Information

## Summary
ClinicEase is a comprehensive medical clinic management system built with Python and Flask. It provides features for patient management, waiting queue, medical visits, diagnoses, and prescription management with PDF printing capabilities. The system supports multiple user roles (doctors and secretaries) and includes an Arabic interface.

## Structure
- **clinic_app/**: Main application package containing all modules
  - **auth/**: Authentication module with login/logout functionality
  - **doctor/**: Doctor-specific features (patient visits, prescriptions)
  - **secretary/**: Secretary-specific features (patient registration, queue management)
  - **main/**: Core application routes and shared functionality
  - **static/**: Static assets (CSS, JavaScript, sounds, prescription templates)
  - **templates/**: HTML templates organized by module
- **instance/**: Contains the SQLite database
- **run.py**: Application entry point
- **update_db.py**: Database update utility
- **create_users.py**: User creation utility

## Language & Runtime
**Language**: Python
**Version**: 3.10.13 (specified in runtime.txt) and 3.11.6 (specified in .python-version)
**Framework**: Flask 2.2.5
**Database**: SQLAlchemy with SQLite

## Dependencies
**Main Dependencies**:
- Flask==2.2.5
- Flask-Login==0.6.3
- Flask-SQLAlchemy>=3.0.0
- Flask-WTF==1.0.1
- reportlab==4.0.4 (for PDF generation)
- arabic-reshaper==3.0.0
- python-bidi==0.4.2
- sqlmodel==0.0.24

**Development Dependencies**:
- python-dotenv==1.0.0

## Build & Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py

# Alternative setup and run (Windows)
setup_and_run.bat
```

## Deployment
**Platform**: Render
**Configuration**: render.yaml
**Runtime**: Python 3.10
**Start Command**: gunicorn run:app
**Environment**: Production

## Database
**Type**: SQLite
**Models**:
- User: Authentication and role management
- Patient: Patient information
- Ticket: Waiting queue management
- Visit: Medical visit records
- Prescription: Medical prescriptions
- Medication: Available medications
- DoctorSettings: Doctor-specific configurations

## Application Structure
**Architecture**: Flask Blueprint-based modular design
**Entry Point**: run.py creates the Flask application
**Blueprints**:
- auth: User authentication
- doctor: Doctor-specific functionality
- secretary: Secretary-specific functionality
- main: Core application routes

## Features
- Multi-role authentication system (doctors and secretaries)
- Patient management and waiting queue
- Medical visit records and diagnoses
- Prescription system with PDF printing
- Waiting room display screen
- Arabic language support with bidirectional text