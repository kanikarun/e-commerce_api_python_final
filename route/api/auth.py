import json
import re

from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import false
from werkzeug.security import check_password_hash

from app import app, db, jwt
from model.customer import Customer
from werkzeug.security import check_password_hash, generate_password_hash

def is_valid_password(password):
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("a lowercase letter")
    if not re.search(r"[0-9]", password):
        errors.append("a number")
    if not re.search(r"[@$!%*?&]", password):
        errors.append("a special character (@$!%*?&)")
    if re.search(r"\s", password):
        errors.append("no spaces allowed")

    if errors:
        if len(errors) == 1:
            message = errors[0]
        else:
            message = ", ".join(errors[:-1]) + " and " + errors[-1]
        return "Password is missing: " + message

    return None

@app.post('/create-customer')
def create_customer():
    customer = request.get_json()
    if not customer:
        return jsonify({'message': 'No user provided!'}), 400

    username = customer.get('username')
    password = customer.get('password')


    if not customer.get('username'):
        return jsonify({'message': 'username is required'}), 400
    if not customer.get('password'):
        return jsonify({'message': 'password is required'}), 400

    password_error = is_valid_password(password)
    if password_error:
        return jsonify({'message': password_error}), 400



    customer_obj = Customer(username=username, password=generate_password_hash(password))
    db.session.add(customer_obj)
    db.session.commit()



    return {
        'message': 'Customer created successfully',
        "customer": {
            'id' : customer_obj.id,
            'username': customer_obj.username,

        }

    }
@app.post('/login')
def login():
    data = request.get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    customers = Customer.query.filter_by(username=username).all()

    if not customers:
        return jsonify({'message': 'Invalid username or password'}), 401

    for customer in customers:
        if check_password_hash(customer.password, password):
            access = create_access_token(identity=str(customer.id))
            return jsonify({
                'message': 'Login successful',
                'access_token': access
            }), 200

    return jsonify({'message': 'Invalid username or password'}), 401

@app.post('/logout')
@jwt_required()
def logout():
    customer_id = get_jwt_identity()
    claims = get_jwt()

    return jsonify({
        "message": "Logout successful"

    }), 200

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.post('/admin/login')
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = create_access_token(identity=json.dumps({"id": 1, "role": "admin"}))
        return {"token": token}, 200

    return {"message": "Invalid username or password"}, 401

@app.post('/admin/logout')
@jwt_required()
def admin_logout():
    identity = get_jwt_identity()

    if not isinstance(identity, str):
        return jsonify({'message': 'Admin access required'}), 403

    admin = json.loads(identity)

    if admin.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    return jsonify({
        "message": "Logout successful"
    }), 200



@app.get("/me")
@jwt_required()
def me():
    customer_id = get_jwt_identity()
    claims = get_jwt()
    return jsonify({
        "id": customer_id,
        "username": claims.get("username"),
    })



