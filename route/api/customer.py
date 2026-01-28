import json
import re

from werkzeug.security import generate_password_hash

from app import app, db
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

from model import Customer
from route.api.auth import is_valid_password

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


@app.get('/admin/customer/list')
@jwt_required()
def admin_get_customers():
    current_user = json.loads(get_jwt_identity())

    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    customers = Customer.query.all()

    if not customers:
        return jsonify({
            'message': 'Customer list is empty',
            'customers': []
        }), 200

    customer_list = [{
        'id': c.id,
        'username': c.username
    } for c in customers]

    return jsonify({
        'customers': customer_list
    }), 200

@app.post('/admin/create-customer')
@jwt_required()
def admin_create_customer():
    current_user = json.loads(get_jwt_identity())

    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username:
        return jsonify({'message': 'Username is required'}), 400
    if not password:
        return jsonify({'message': 'Password is required'}), 400

    password_error = is_valid_password(password)
    if password_error:
        return jsonify({'message': password_error}), 400


    customer_obj = Customer(
        username=username,
        password=generate_password_hash(password)
    )
    db.session.add(customer_obj)
    db.session.commit()

    return {
        'message': 'Customer created successfully',
        'customer': {
            'id': customer_obj.id,
            'username': customer_obj.username,
        }
    }, 201



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

@app.put('/admin/customer/update/<int:customer_id>')
@jwt_required()
def admin_update_customer(customer_id):

    current_user = json.loads(get_jwt_identity())
    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404

    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({'message': 'Request body is required'}), 400

    username = data.get('username')
    password = data.get('password')

    if username:
        customer.username = username.strip()

    if password:
        password_error = is_valid_password(password)
        if password_error:
            return jsonify({'message': password_error}), 400
        customer.password = generate_password_hash(password)

    db.session.commit()

    return jsonify({
        'message': 'Customer updated successfully',
        'customer': {
            'id': customer.id,
            'username': customer.username
        }
    }), 200

@app.delete('/admin/customer/delete/<int:customer_id>')
@jwt_required()
def admin_delete_customer(customer_id):

    current_user = json.loads(get_jwt_identity())
    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()

    return jsonify({
        'message': 'Customer deleted successfully',
    }), 200
