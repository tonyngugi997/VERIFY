from flask import request, render_template, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
import uuid
from models import get_user_by_username, get_db_connection, get_setting
from auth import staff_required, admin_required, User
from user_agents import parse as parse_user_agent

def register_routes(app):
    pass