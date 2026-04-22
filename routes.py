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
            
        else:  
            name_term = request.form.get('id_number', '').strip()
            
            if not name_term:
                return render_template('index.html', result={
                    'status': 'ERROR',
                    'message': 'Please enter a name to search.'
                })
            
            if len(name_term) < 2:
                return render_template('index.html', result={
                    'status': 'ERROR',
                    'message': 'Please enter at least 2 characters for name search.'
                })
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, gender, size, phone_number, cohort_number, education_level FROM recruitees WHERE LOWER(name) LIKE ? LIMIT 1",
                (f'%{name_term.lower()}%',)
            )
            existing = cursor.fetchone()
            conn.close()
        
        if existing:
            return render_template('index.html', result={
                'status': 'REJECTED',
                'message': f"{existing['name']} is already in Cohort {existing['cohort_number']}.",
                'details': {
                    'name': existing['name'],
                    'gender': existing['gender'],
                    'size': existing['size'],
                    'phone': existing['phone_number'],
                    'cohort': existing['cohort_number'],
                    'education': existing['education_level']
                }
            })
        else:
            current_cohort = get_setting('current_cohort', '9')
            return render_template('index.html', result={
                'status': 'APPROVED',
                'message': f"Clear for registration in Cohort {current_cohort}."
            })
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            parsed_ua = parse_user_agent(user_agent)
            device_info = f"{parsed_ua.browser.family} on {parsed_ua.os.family}"
            
            from models import get_failed_attempt_count
            failed_count = get_failed_attempt_count(username, 15)
            
            if failed_count >= 5:
                flash('Too many failed login attempts. Please try again after 15 minutes.', 'error')
                from models import log_login_attempt
                log_login_attempt(None, username, ip_address, user_agent, False, 'Rate limit exceeded')
                return render_template('login.html')
            
            if not username or not password:
                flash('Please enter username and password.', 'error')
                return render_template('login.html')
            
            user = get_user_by_username(username)
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['hashed_password'].encode('utf-8')):
                from models import log_login_attempt, create_active_session
                
                log_login_attempt(user['id'], username, ip_address, user_agent, True, None)
                
                user_obj = User(user['id'], user['username'], user['role'])
                login_user(user_obj, remember=True)
                
                session_id = request.cookies.get('session', '') or str(uuid.uuid4())
                create_active_session(user['id'], session_id, ip_address, user_agent, device_info)
                
                flash(f'Welcome back, {username}!', 'success')
                return redirect(url_for('index'))
            else:
                from models import log_login_attempt
                failure_reason = 'Invalid username or password'
                log_login_attempt(user['id'] if user else None, username, ip_address, user_agent, False, failure_reason)
                flash('Invalid username or password.', 'error')
                return render_template('login.html')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        from models import deactivate_session_on_logout
        session_id = request.cookies.get('session', '')
        if session_id:
            deactivate_session_on_logout(session_id)
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/debug/ids')
    @admin_required
    def debug_ids():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_number, name, cohort_number FROM recruitees LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])
    
    @app.route('/search/names', methods=['GET'])
    @staff_required
    def search_names():
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_number, name, gender, size, phone_number, cohort_number, education_level FROM recruitees WHERE LOWER(name) LIKE ? LIMIT 10",
            (f'%{query.lower()}%',)
        )
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])

    @app.route('/admin/staff')
    @admin_required
    def admin_staff():
        from models import get_all_users
        users = get_all_users()
        return render_template('admin_staff.html', users=users, current_user=current_user)
    
    @app.route('/admin/staff/add', methods=['POST'])
    @admin_required
    def admin_add_user():
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'staff')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('admin_staff'))
        
        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'error')
            return redirect(url_for('admin_staff'))
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        from models import create_user
        success = create_user(username, hashed.decode('utf-8'), role)
        
        if success:
            flash(f'User "{username}" created successfully as {role}.', 'success')
        else:
            flash(f'Username "{username}" already exists.', 'error')
        
        return redirect(url_for('admin_staff'))
    
    @app.route('/admin/staff/delete/<int:user_id>')
    @admin_required
    def admin_delete_user(user_id):
        current_user_id = int(current_user.id)
        target_user_id = int(user_id)
        
        if target_user_id == current_user_id:
            flash('❌ You cannot delete your own account. This action has been blocked.', 'error')
            return redirect(url_for('admin_staff'))
        
        from models import delete_user_by_id
        if delete_user_by_id(target_user_id):
            flash(f'✅ User deleted successfully.', 'success')
        else:
            flash(f'❌ User not found or could not be deleted.', 'error')
        
        return redirect(url_for('admin_staff'))

    @app.route('/admin/database')
    @admin_required
    def admin_database():
        from models import get_all_recruitees
        recruitees = get_all_recruitees()
        return render_template('admin_database.html', recruitees=recruitees)

    @app.route('/admin/database/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_recruitee():
        if request.method == 'POST':
            id_number = request.form.get('id_number', '').strip()
            name = request.form.get('name', '').strip()
            gender = request.form.get('gender', '')
            size = request.form.get('size', '')
            phone = request.form.get('phone', '').strip()
            cohort = request.form.get('cohort', '').strip()
            education = request.form.get('education', '')
            
            if not id_number or not name or not cohort:
                flash('ID Number, Name, and Cohort are required.', 'error')
                return redirect(url_for('admin_add_recruitee'))
            
            if not id_number.isdigit():
                flash('ID Number must contain only digits.', 'error')
                return redirect(url_for('admin_add_recruitee'))
            if len(id_number) < 6 or len(id_number) > 10:
                flash('ID Number must be between 6 and 10 digits.', 'error')
                return redirect(url_for('admin_add_recruitee'))
            
            from models import add_recruitee
            success = add_recruitee(id_number, name, gender, size, phone, cohort, education)
            if success:
                flash(f'Recruitee {name} added successfully.', 'success')
                return redirect(url_for('admin_database'))
            else:
                flash(f'ID Number {id_number} already exists.', 'error')
                return redirect(url_for('admin_add_recruitee'))
        
        return render_template('admin_database_form.html', action='Add', recruitee=None)

    @app.route('/admin/database/edit/<id_number>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_recruitee(id_number):
        from models import get_recruitee_by_id, update_recruitee
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            gender = request.form.get('gender', '')
            size = request.form.get('size', '')
            phone = request.form.get('phone', '').strip()
            cohort = request.form.get('cohort', '').strip()
            education = request.form.get('education', '')
            
            if not name or not cohort:
                flash('Name and Cohort are required.', 'error')
                return redirect(url_for('admin_edit_recruitee', id_number=id_number))
            
            success = update_recruitee(id_number, name, gender, size, phone, cohort, education)
            if success:
                flash(f'Recruitee {name} updated successfully.', 'success')
                return redirect(url_for('admin_database'))
            else:
                flash('Update failed.', 'error')
                return redirect(url_for('admin_edit_recruitee', id_number=id_number))
        
        recruitee = get_recruitee_by_id(id_number)
        if not recruitee:
            flash('Recruitee not found.', 'error')
            return redirect(url_for('admin_database'))
        return render_template('admin_database_form.html', action='Edit', recruitee=recruitee)

    @app.route('/admin/database/delete/<id_number>')
    @admin_required
    def admin_delete_recruitee(id_number):
        from models import delete_recruitee
        if delete_recruitee(id_number):
            flash('Recruitee deleted successfully.', 'success')
        else:
            flash('Recruitee not found.', 'error')
        return redirect(url_for('admin_database'))

    @app.route('/profile')
    @login_required
    def profile():
        from models import get_user_by_id
        user = get_user_by_id(current_user.id)
        return render_template('profile.html', user=user)
    
    @app.route('/profile/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            current_password = request.form.get('current_password', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not current_password or not new_password or not confirm_password:
                flash('All fields are required.', 'error')
                return render_template('change_password.html')
            
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('change_password.html')
            
            if len(new_password) < 4:
                flash('New password must be at least 4 characters.', 'error')
                return render_template('change_password.html')
            
            from models import get_user_by_username
            user = get_user_by_username(current_user.username)
            if not user or not bcrypt.checkpw(current_password.encode('utf-8'), user['hashed_password'].encode('utf-8')):
                flash('Current password is incorrect.', 'error')
                return render_template('change_password.html')
            
            hashed_new = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            from models import update_user_password
            if update_user_password(current_user.id, hashed_new.decode('utf-8')):
                flash('Password changed successfully. Please log in again.', 'success')
                logout_user()
                return redirect(url_for('login'))
            else:
                flash('An error occurred. Please try again.', 'error')
        
        return render_template('change_password.html')
    
    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html')

    @app.route('/settings/sessions-data')
    @login_required
    def settings_sessions_data():
        from models import get_user_active_sessions, get_all_active_sessions
        if current_user.is_admin:
            sessions = get_all_active_sessions()
            sessions_list = [dict(s) for s in sessions]
        else:
            sessions = get_user_active_sessions(current_user.id)
            sessions_list = []
            for s in sessions:
                s_dict = dict(s)
                s_dict['is_current'] = (s_dict['session_id'] == request.cookies.get('session', ''))
                sessions_list.append(s_dict)
        return jsonify({'sessions': sessions_list})

    @app.route('/settings/login-history-data')
    @login_required
    def settings_login_history_data():
        from models import get_user_login_history, get_all_login_history
        if current_user.is_admin:
            history = get_all_login_history(100)
        else:
            history = get_user_login_history(current_user.id, 50)
        return jsonify({'history': [dict(h) for h in history]})

    @app.route('/settings/logout-others', methods=['POST'])
    @login_required
    def settings_logout_others():
        from models import logout_other_sessions
        current_session_id = request.cookies.get('session', '')
        count = logout_other_sessions(current_user.id, current_session_id)
        return jsonify({'success': True, 'count': count})