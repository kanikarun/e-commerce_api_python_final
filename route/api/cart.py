from urllib import request

from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import app, db
from model import Product, Cart


@app.post('/api/cart')
@jwt_required()
def add_to_cart():
    customer_id = get_jwt_identity()
    data = request.get_json(silent=True) or request.form

    product_id = data.get('product_id')
    qty = data.get('qty', 1)

    if not product_id:
        return jsonify({'message': 'Product ID is required'}), 400

    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return jsonify({'message': 'Product ID must be an integer'}), 400

    try:
        qty = int(qty)
    except (ValueError, TypeError):
        return jsonify({'message': 'qty must be an integer'}), 400

    if qty < 1:
        return jsonify({'message': 'qty must be greater than 0'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    try:
        stock = int(product.stock)
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid product stock value'}), 500

    if stock < qty:
        return jsonify({'message': 'Insufficient stock'}), 400

    cart_item = Cart.query.filter_by(
        customer_id=customer_id,
        product_id=product_id
    ).first()

    if cart_item:
        cart_item.qty += qty
    else:
        cart_item = Cart(
            customer_id=customer_id,
            product_id=product_id,
            qty=qty
        )
        db.session.add(cart_item)

    db.session.commit()

    return jsonify({
        'cart_item': {
            'id': cart_item.id,
            'product': product.title,
            'qty': cart_item.qty,
            'price': product.price,
            'subtotal': product.price * cart_item.qty
        }
    }), 200

@app.get('/api/cart/list')
@jwt_required()
def get_cart_list():
    customer_id = get_jwt_identity()
    cart_items = Cart.query.filter_by(customer_id=customer_id).all()
    if not cart_items:
        return jsonify({
            'message': 'Cart is empty',
        }), 200

    cart_list = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product:
            continue

        cart_list.append({
            'cart_id': item.id,
            'product': product.title,
            'qty': item.qty,
            'price': product.price,
            'subtotal': product.price * item.qty,
        })

    return jsonify({
        'cart': cart_list
    }), 200


@app.put('/api/cart/<int:item_id>')
@jwt_required()
def update_cart_item(item_id):
    customer_id = get_jwt_identity()

    data = request.get_json(silent=True) or request.form
    qty = data.get('qty')

    if qty is None:
        return jsonify({'message': 'Quantity (qty) is required'}), 400

    try:
        qty = int(qty)
        if qty <= 0:
            return jsonify({'message': 'Quantity must be greater than 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'message': 'Quantity must be an integer'}), 400

    cart_item = Cart.query.filter_by(id=item_id, customer_id=customer_id).first()
    if not cart_item:
        return jsonify({'message': 'Cart item not found'}), 404

    product = Product.query.get(cart_item.product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if qty > product.stock:
        return jsonify({'message': 'Insufficient stock'}), 400

    cart_item.qty = qty
    db.session.commit()

    return jsonify({
        'message': 'Cart item updated successfully',
        'cart_item': {
            'cart_id': cart_item.id,
            'product': product.title,
            'qty': cart_item.qty,
            'price': product.price,
            'subtotal': product.price * cart_item.qty,
        }
    }), 200


@app.delete('/api/cart/<int:item_id>')
@jwt_required()
def delete_cart_item(item_id):
    customer_id = get_jwt_identity()

    cart_item = Cart.query.filter_by(id=item_id, customer_id=customer_id).first()
    if not cart_item:
        return jsonify({'message': 'Cart item not found'}), 404

    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({
        'message': 'Cart item deleted successfully',
    }), 200

