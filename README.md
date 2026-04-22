# Muranga Youth Service Recruitment System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.0+-red.svg)](https://flask.palletsprojects.com/)

## Overview

A production-ready recruitment verification system for **Muranga County Youth Service** that prevents duplicate registrations across multiple cohorts. Staff can instantly verify applicants by ID number or name, while administrators maintain the database and manage user access.

## Key Features

### 🔐 Security
- **Role-Based Access** (Admin/Staff with decorator-based protection)
- **Rate Limiting** - 5 failed login attempts per 15 minutes
- **bcrypt Password Hashing** with salt rounds
- **Session Management** - Track active sessions, force logout remotely
- **Audit Trail** - Complete login history with IP, device, location

### 👥 User Management
- Admin dashboard for staff account management
- Self-service password changes
- Profile viewing with account creation date

### 📊 Recruitment Management
- **Instant Verification** by ID (6-10 digits) or name search
- **Cohort System** - Dynamic current cohort configuration
- **Rejection Details** - Shows existing applicant information
- **CRUD Operations** for recruitees with education level tracking

### 🎨 User Experience
- **Responsive Design** - Mobile, tablet, and desktop optimized
- **Dark/Light Mode** with localStorage persistence
- **Glassmorphism UI** with gradient animations
- **Keyboard Navigation** for search suggestions
- **Toast Notifications** for all actions

### 🔧 Admin Tools
- Database management (add/edit/delete recruitees)
- Staff account management (create/delete users)
- System settings (cohort number configuration)
- Active sessions viewer with force logout capability
- Login history viewer across all users

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 2.0+ |
| Auth | Flask-Login + bcrypt |
| Database | SQLite3 |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Icons | Font Awesome 6 |
| Animations | CSS3 (keyframes, transitions) |

## Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/muranga-youth-recruitment.git
cd muranga-youth-recruitment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app import create_app; create_app()"

# Create admin user
python create_admin.py

# Run application
python app.py
