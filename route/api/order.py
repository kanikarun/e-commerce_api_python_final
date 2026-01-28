import json

from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import app, db
from model import Product, Cart, Order


@app.get('/admin/order')
@jwt_required()
def admin_get_orders():
    current_user = json.loads(get_jwt_identity())
    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    orders = Order.query.order_by(Order.date_time.desc()).all()
    if not orders:
        return jsonify({
            'message': 'No orders found',
            'orders': []
        }), 200

    order_list = []
    for order in orders:
        order_list.append({
            'id': order.id,
            'customer_id': order.customer_id,
            'total': order.total,
            'status': order.status,
            'paid': order.paid,
            'paid_by': order.paid_by,
            'date_time': order.date_time,
            'details': [{
                'product_id': d.product_id,
                'qty': d.qty,
                'price': d.price,
                'cost': d.cost
            } for d in order.details]
        })

    return jsonify({'orders': order_list}), 200



@app.get('/admin/order/detail/<int:order_id>')
@jwt_required()
def admin_get_order_detail(order_id):
    current_user = json.loads(get_jwt_identity())
    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    order_data = {
        'id': order.id,
        'customer_id': order.customer_id,
        'total': order.total,
        'status': order.status,
        'paid': order.paid,
        'paid_by': order.paid_by,
        'date_time': order.date_time,
        'details': []
    }

    for d in order.details:
        product = Product.query.get(d.product_id)
        order_data['details'].append({
            'product_id': d.product_id,
            'product_title': product.title if product else None,
            'qty': d.qty,
            'price': d.price,
            'cost': d.cost,
            'subtotal': d.qty * d.price
        })

    return jsonify({'order': order_data}), 200

@app.put('/admin/order/update/<int:order_id>')
@jwt_required()
def admin_update_order(order_id):
    current_user = json.loads(get_jwt_identity())
    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    data = request.get_json(silent=True) or request.form
    status = data.get('status')
    paid = data.get('paid')
    paid_by = data.get('paid_by')

    if not status and paid is None and not paid_by:
        return jsonify({'message': 'At least one field (status, paid, paid_by) is required'}), 400

    if status:
        order.status = status.strip().lower()  # normalize status if needed

    if paid is not None:
        if isinstance(paid, str):
            if paid.lower() in ['true', '1']:
                paid = True
            elif paid.lower() in ['false', '0']:
                paid = False
            else:
                return jsonify({'message': 'paid must be true or false'}), 400
        elif not isinstance(paid, bool):
            return jsonify({'message': 'paid must be true or false'}), 400

        order.paid = paid

    if paid_by:
        order.paid_by = paid_by.strip()

    db.session.commit()

    return jsonify({
        'message': 'Order updated successfully',
        'order': {
            'id': order.id,
            'customer_id': order.customer_id,
            'status': order.status,
            'paid': order.paid,
            'paid_by': order.paid_by,
            'total': order.total,
            'date_time': order.date_time
        }
    }), 200


@app.get('/order/<int:order_id>')
@jwt_required()
def track_order(order_id):
    customer_id = get_jwt_identity()

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    try:
        customer_id = int(customer_id)
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid customer token'}), 400

    if order.customer_id != customer_id:
        return jsonify({'message': 'Order not found'}), 403

    order_data = {
        'id': order.id,
        'total': order.total,
        'status': order.status,
        'paid': order.paid,
        'paid_by': order.paid_by,
        'date_time': order.date_time,
        'details': []
    }

    for d in order.details:
        product = Product.query.get(d.product_id)
        order_data['details'].append({
            'product': product.title if product else None,
            'qty': d.qty,
            'price': d.price,
            'subtotal': d.qty * d.price
        })

    return jsonify({'order': order_data}), 200


