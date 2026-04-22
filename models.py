import sqlite3
from config import DATABASE_PATH
from datetime import datetime

def get_db_connection():
    """Creates and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Create all tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ===== EXISTING TABLES =====
    
    # Recruitees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recruitees (
            id_number TEXT PRIMARY KEY,
            name TEXT,
            gender TEXT,
            size TEXT,
            phone_number TEXT,
            cohort_number INTEGER,
            education_level TEXT
        )
    ''')
    
    # Users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('staff', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== NEW TABLES FOR SESSIONS & LOGGING =====
    
    # Login history table - tracks all login attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL,
            ip_address TEXT,
            location TEXT,
            user_agent TEXT,
            success INTEGER DEFAULT 0,
            failure_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Active sessions table - tracks currently logged in sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            location TEXT,
            device_info TEXT,
            user_agent TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # System settings table - stores global app settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default system settings if not exists
    cursor.execute('''
        INSERT OR IGNORE INTO system_settings (setting_key, setting_value)
        VALUES ('current_cohort', '9')
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database tables ready: recruitees, users, login_history, active_sessions, system_settings")

# ===== EXISTING USER FUNCTIONS (unchanged) =====

def get_user_by_username(username):
    """Fetch a user by username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    """Fetch all users (excluding passwords)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    return users

def create_user(username, hashed_password, role):
    """Create a new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_user_by_id(user_id):
    """Delete a user by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def update_user_password(user_id, hashed_password):
    """Update a user's password"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET hashed_password = ? WHERE id = ?", (hashed_password, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_user_by_id(user_id):
    """Fetch a user by ID (excludes password)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# ===== EXISTING RECRUITEE FUNCTIONS (unchanged) =====

def get_all_recruitees(limit=100):
    """Fetch all recruitees (for admin listing)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_number, name, gender, size, phone_number, cohort_number, education_level FROM recruitees ORDER BY cohort_number, name LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_recruitee_by_id(id_number):
    """Fetch a single recruitee by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recruitees WHERE id_number = ?", (id_number,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_recruitee(id_number, name, gender, size, phone_number, cohort_number, education_level=None):
    """Add a new recruitee"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO recruitees (id_number, name, gender, size, phone_number, cohort_number, education_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id_number, name, gender, size, phone_number, cohort_number, education_level)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_recruitee(id_number, name, gender, size, phone_number, cohort_number, education_level=None):
    """Update an existing recruitee"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE recruitees SET name = ?, gender = ?, size = ?, phone_number = ?, cohort_number = ?, education_level = ? WHERE id_number = ?",
        (name, gender, size, phone_number, cohort_number, education_level, id_number)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def delete_recruitee(id_number):
    """Delete a recruitee by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recruitees WHERE id_number = ?", (id_number,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# ===== NEW: LOGIN HISTORY FUNCTIONS =====

def log_login_attempt(user_id, username, ip_address, user_agent, success, failure_reason=None):
    """Log a login attempt (successful or failed)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Simple location placeholder (can be enhanced with IP geolocation later)
    location = 'Unknown'
    
    cursor.execute('''
        INSERT INTO login_history (user_id, username, ip_address, location, user_agent, success, failure_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, ip_address, location, user_agent, 1 if success else 0, failure_reason))
    
    conn.commit()
    conn.close()

def get_user_login_history(user_id, limit=50):
    """Get login history for a specific user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, ip_address, location, success, failure_reason, created_at
        FROM login_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_login_history(limit=100):
    """Get all login history (admin only)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, ip_address, location, success, failure_reason, created_at
        FROM login_history
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_failed_attempt_count(username, minutes=15):
    """Get number of failed login attempts in last X minutes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM login_history
        WHERE username = ? AND success = 0 AND created_at > datetime('now', '-' || ? || ' minutes')
    ''', (username, minutes))
    result = cursor.fetchone()
    conn.close()
    return result['count'] if result else 0

def clear_failed_attempts(username):
    """Clear failed login attempts for a user (called after successful login)"""
    # This is optional - we just rely on the time window
    pass

# ===== NEW: ACTIVE SESSIONS FUNCTIONS =====

def create_active_session(user_id, session_id, ip_address, user_agent, device_info):
    """Create a new active session record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    location = 'Unknown'
    
    cursor.execute('''
        INSERT INTO active_sessions (user_id, session_id, ip_address, location, device_info, user_agent, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (user_id, session_id, ip_address, location, device_info, user_agent))
    
    conn.commit()
    conn.close()

def update_session_activity(session_id):
    """Update last_activity timestamp for a session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE active_sessions
        SET last_activity = CURRENT_TIMESTAMP
        WHERE session_id = ?
    ''', (session_id,))
    conn.commit()
    conn.close()

def get_user_active_sessions(user_id):
    """Get all active sessions for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, session_id, ip_address, location, device_info, login_time, last_activity
        FROM active_sessions
        WHERE user_id = ? AND is_active = 1
        ORDER BY login_time DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_active_sessions():
    """Get all active sessions across all users (admin only)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.session_id, s.ip_address, s.location, s.device_info, s.login_time, s.last_activity, u.username, u.role
        FROM active_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.is_active = 1
        ORDER BY s.login_time DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def logout_other_sessions(user_id, current_session_id):
    """Logout all other sessions for a user except current one"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE active_sessions
        SET is_active = 0
        WHERE user_id = ? AND session_id != ?
    ''', (user_id, current_session_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected

def force_logout_user_session(session_id):
    """Force logout a specific session (admin only)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE active_sessions
        SET is_active = 0
        WHERE session_id = ?
    ''', (session_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected

def deactivate_session_on_logout(session_id):
    """Deactivate session when user logs out"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE active_sessions
        SET is_active = 0
        WHERE session_id = ?
    ''', (session_id,))
    conn.commit()
    conn.close()

# ===== NEW: SYSTEM SETTINGS FUNCTIONS =====

def get_setting(key, default=None):
    """Get a system setting value"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result['setting_value'] if result else default

def update_setting(key, value):
    """Update a system setting"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE system_settings
        SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE setting_key = ?
    ''', (value, key))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


import requests

def get_ip_location(ip_address):
    """Get location from IP address using free API"""
    if ip_address == '127.0.0.1' or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
        return 'Local Network'
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=2)
        data = response.json()
        if data.get('status') == 'success':
            city = data.get('city', '')
            country = data.get('countryCode', '')
            if city and country:
                return f'{city}, {country}'
            elif city:
                return city
            elif country:
                return country
        return 'Unknown'
    except:
        return 'Unknown'