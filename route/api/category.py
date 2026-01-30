import json

from flask_jwt_extended import get_jwt_identity, jwt_required

from app import app,db
from flask import request, jsonify
from model import Category


@app.post('/admin/category/create')
@jwt_required()
def create_category():
    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    data = request.get_json()

    name = data.get('name')
    if not name:
        return jsonify({'message': 'Category name is required'}), 400

    if Category.query.filter_by(name=name).first():
        return jsonify({'message': 'Category already exists'}), 400

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()

    return jsonify({
        'message': 'Category created successfully',
        'category': {
            'id': category.id,
            'name': category.name
        }
    }), 201

@app.get('/admin/category/list/')
@jwt_required()
def get_categories():
    current_user = json.loads(get_jwt_identity())

    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    categories = Category.query.all()

    if not categories:
        return jsonify({'message': 'Category list is empty'}), 404

    return jsonify({
        'categories': [
            {
                'id': c.id,
                'name': c.name
            } for c in categories
        ]
    }), 200


@app.put('/admin/category/update/<int:category_id>')
@jwt_required()
def update_category(category_id):
    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    data = request.get_json()
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'message': 'Category not found'}), 404

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'message': 'Category name is required'}), 400
    name = name.strip()

    existing_category = Category.query.filter(
        Category.name.ilike(name),
        Category.id != category_id
    ).first()

    if existing_category:
        return jsonify({
            'message': f"Category '{name}' already exists"
        }), 400

    category.name = name
    db.session.commit()

    return jsonify({
        'message': 'Category updated successfully',
        'category': {
            'id': category.id,
            'name': category.name
        }
    })

@app.delete('/admin/category/delete/<int:category_id>')
@jwt_required()
def delete_category(category_id):
    current_user = json.loads(get_jwt_identity())

    if current_user.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    category = Category.query.get(category_id)
    if not category:
        return jsonify({'message': 'Category not found'}), 404

    # Prevent delete if products exist
    if category.products:
        return jsonify({
            'message': 'Cannot delete category because it contains products'
        }), 409

    db.session.delete(category)
    db.session.commit()

    return jsonify({'message': 'Category deleted successfully'}), 200
