from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import app, db
from model import Product, Cart, Order, OrderDetail


@app.post('/api/checkout')
@jwt_required()
def checkout():
    customer_id = get_jwt_identity()

    cart_items = Cart.query.filter_by(customer_id=customer_id).all()
    if not cart_items:
        return jsonify({'message': 'Cart is empty'}), 400

    total = 0
    order_details = []

    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product:
            return jsonify({'message': 'Product not found'}), 404

        if item.qty > product.stock:
            return jsonify({
                'message': f'Insufficient stock for {product.title}'
            }), 400

        subtotal = product.price * item.qty
        total += subtotal

        order_details.append({
            'product': product,
            'qty': item.qty
        })

    order = Order(
        customer_id=customer_id,
        total=total,
        status='pending',
        paid=False
    )
    db.session.add(order)
    db.session.flush()  # get order.id before commit

    for item in order_details:
        detail = OrderDetail(
            order_id=order.id,
            product_id=item['product'].id,
            qty=item['qty'],
            cost=item['product'].cost,
            price=item['product'].price
        )
        db.session.add(detail)

        item['product'].stock -= item['qty']

    Cart.query.filter_by(customer_id=customer_id).delete()

    db.session.commit()

    return jsonify({
        'message': 'Checkout successful',
        'order': {
            'order_id': order.id,
            'total': order.total,
            'status': order.status,
            'paid': order.paid
        }
    }), 201
