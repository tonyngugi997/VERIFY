from flask import request, render_template, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
import uuid
from models import get_user_by_username, get_db_connection, get_setting
from auth import staff_required, admin_required, User
from user_agents import parse as parse_user_agent

def register_routes(app):
    
    @app.route('/')
    @staff_required
    def index():
        return render_template('index.html', result=None)
    
    @app.route('/verify', methods=['POST'])
    @staff_required
    def verify():
        search_type = request.form.get('search_type', 'id')
        
        if search_type == 'id':
            id_number = request.form.get('id_number', '').strip()
            
            if not id_number:
                return render_template('index.html', result={
                    'status': 'ERROR',
                    'message': 'Please enter an ID number.'
                })
            
            if not id_number.isdigit():
                return render_template('index.html', result={
                    'status': 'ERROR',
                    'message': 'ID number must contain only digits (0-9).'
                })
            
            # Dynamic ID length: 6 to 10 digits
            if len(id_number) < 6 or len(id_number) > 10:
                return render_template('index.html', result={
                    'status': 'ERROR',
                    'message': 'ID number must be between 6 and 10 digits.'
                })
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, gender, size, phone_number, cohort_number, education_level FROM recruitees WHERE id_number = ?",
                (id_number,)
            )
            existing = cursor.fetchone()
            conn.close()