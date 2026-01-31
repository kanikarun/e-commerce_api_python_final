import json
import os
import uuid

from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename
from app import app,db
from flask import request, jsonify, send_from_directory, url_for
from model import Category, Product

UPLOAD_FOLDER = r'D:\SU33\ADV Python\Final\ecom_api\uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def get_image_url(image):
    if not image:
        return None

    # If already correct full URL
    if image.startswith("https://") and "/static/uploads/" in image:
        return image

    # 🔥 FIX OLD LOCAL URLs
    image = image.replace("http://127.0.0.1:5000/uploads/", "")
    image = image.replace("http://localhost:5000/uploads/", "")

    # 🔥 FIX OLD PATH FORMATS
    image = image.replace("static/uploads/", "")
    image = image.replace("/uploads/", "")
    image = image.replace("uploads/", "")

    return url_for(
        "static",
        filename=f"uploads/{image}",
        _external=True
    )


# admin panel
@app.post('/admin/product/create')
@jwt_required()
def create_product():
    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    title = request.form.get('title')
    price = request.form.get('price')
    cost = request.form.get('cost')
    stock = request.form.get('stock')
    description = request.form.get('description')
    category_id = request.form.get('category_id')

    missing_fields = []
    invalid_fields = []

    if not title or title.strip() == "":
        missing_fields.append('title')
    else:
        existing_product = Product.query.filter_by(title=title.strip()).first()
        if existing_product:
            return jsonify({'message': f"A product with the title '{title}' already exists"}), 400
    if not price or str(price).strip() == "":
        missing_fields.append('price')
    if not cost or str(cost).strip() == "":
        missing_fields.append('cost')
    if not stock or str(stock).strip() == "":
        missing_fields.append('stock')
    if not category_id or str(category_id).strip() == "":
        missing_fields.append('category_id')

    if price and str(price).strip() != "":
        try:
            price = float(price)
        except (ValueError, TypeError):
            invalid_fields.append('price')

    if cost and str(cost).strip() != "":
        try:
            cost = float(cost)
        except (ValueError, TypeError):
            invalid_fields.append('cost')

    try:
        stock = int(stock)
    except (ValueError, TypeError):
        return jsonify({'message': 'Stock must be an integer'}), 400

    messages = []

    if missing_fields:
        if len(missing_fields) == 1:
            messages.append(f"Missing required field: {missing_fields[0]}")
        else:
            messages.append("Missing required fields: " + ', '.join(missing_fields[:-1]) + " and " + missing_fields[-1])

    if invalid_fields:
        if len(invalid_fields) == 1:
            messages.append(f"{invalid_fields[0]} must be a number")
        else:
            messages.append(', '.join(invalid_fields[:-1]) + " and " + invalid_fields[-1] + " must be numbers")

    if messages:
        return jsonify({'message': '; '.join(messages)}), 400

    category = Category.query.get(category_id)
    if not category:
        return jsonify({'message': 'Category not found'}), 404

    image_file = request.files.get('image')
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        image_file.save(save_path)
        image_url = request.host_url.rstrip('/') + f"/uploads/{unique_filename}"
    else:
        image_url = None


    product = Product(
        title=title,
        price=price,
        cost=cost,
        stock=stock,
        description=description,
        image=image_url,
        category_id=category_id
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({
        'message': 'Product created successfully',
        'product': {
            'id': product.id,
            'title': product.title,
            'cost': product.cost,
            'price': product.price,
            'stock': product.stock,
            'description': product.description,
            'image': product.image,
            'category': category.name

        }
    }), 201

@app.put('/admin/product/update')
@jwt_required()
def update_product():
    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    product_id = request.form.get('id')
    if not product_id:
        return jsonify({'message': 'Product ID is required'}), 400

    try:
        product_id = int(product_id)
    except ValueError:
        return jsonify({'message': 'Product ID must be an integer'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    title = request.form.get('title')
    if title:
        title_clean = title.strip()
        existing_product = Product.query.filter(
            Product.title.ilike(title_clean),
            Product.id != product_id
        ).first()

        if existing_product:
            return jsonify({'message': f"A product with the title '{title_clean}' already exists"}), 400

        product.title = title_clean


    title = request.form.get('title')
    price = request.form.get('price')
    cost = request.form.get('cost')
    stock = request.form.get('stock')
    description = request.form.get('description')
    category_id = request.form.get('category_id')

    invalid_fields = []

    if price is not None:
        try:
            price = float(price)
            product.price = price
        except:
            invalid_fields.append('price')

    if cost is not None:
        try:
            cost = float(cost)
            product.cost = cost
        except:
            invalid_fields.append('cost')

    if stock is not None:
        try:
            stock = int(stock)
            product.stock = stock
        except (ValueError, TypeError):
            return jsonify({'message': 'stock must be an integer'}), 400

    if category_id is not None:
        try:
            category_id = int(category_id)
        except:
            invalid_fields.append('category_id')
        else:
            category = Category.query.get(category_id)
            if not category:
                return jsonify({'message': 'Category not found'}), 404
            product.category_id = category_id

    if invalid_fields:
        return jsonify({
            'message': ', '.join(invalid_fields) + ' must be a number'
        }), 400

    if title is not None and title.strip() != "":
        product.title = title

    if description is not None:
        product.description = description

    image_file = request.files.get('image')
    if image_file and allowed_file(image_file.filename):

        if product.image:
            old_filename = product.image.split('/uploads/')[-1]
            old_path = os.path.join(UPLOAD_FOLDER, old_filename)

            if os.path.exists(old_path):
                os.remove(old_path)

        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        image_file.save(save_path)

        product.image = request.host_url.rstrip('/') + f"/uploads/{unique_filename}"

    db.session.commit()

    return jsonify({
        'message': 'Product updated successfully',
        'product': {
            'id': product.id,
            'title': product.title,
            'price': product.price,
            'cost': product.cost,
            'stock': product.stock,
            'image': product.image,
            'description': product.description,
            'category': product.category.name if product.category else None
        }
    }), 200

@app.put('/admin/product/update/<int:id>')
@jwt_required()
def update_product_by_id(id):

    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    product = Product.query.get(id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    title = request.form.get('title')
    if title:
        title_clean = title.strip()
        existing_product = Product.query.filter(
            Product.title.ilike(title_clean),
        ).first()

        if existing_product:
            return jsonify({'message': f"A product with the title '{title_clean}' already exists"}), 400

        product.title = title_clean

    title = request.form.get('title')
    price = request.form.get('price')
    cost = request.form.get('cost')
    stock = request.form.get('stock')
    description = request.form.get('description')
    category_id = request.form.get('category_id')

    messages = []

    if price is not None:
        try:
            price = float(price)
            product.price = price
        except (ValueError, TypeError):
            messages.append('price must be a number')

    if cost is not None:
        try:
            cost = float(cost)
            product.cost = cost
        except (ValueError, TypeError):
            messages.append('cost must be a number')

    if stock is not None:
        try:
            stock = int(stock)
            product.stock = stock
        except (ValueError, TypeError):
            messages.append('stock must be an integer')

    if category_id is not None:
        try:
            category_id = int(category_id)
            category = Category.query.get(category_id)
            if not category:
                return jsonify({'message': 'Category not found'}), 404
            product.category_id = category_id
        except (ValueError, TypeError):
            messages.append('category_id must be an integer')

    if messages:
        return jsonify({'message': '; '.join(messages)}), 400

    if title is not None and title.strip() != "":
        product.title = title
    if description is not None:
        product.description = description

    image_file = request.files.get('image')
    if image_file and allowed_file(image_file.filename):
        # Delete old image
        if product.image:
            old_filename = product.image.split('/uploads/')[-1]
            old_path = os.path.join(UPLOAD_FOLDER, old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)

        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        image_file.save(save_path)
        product.image = request.host_url.rstrip('/') + f"/uploads/{unique_filename}"

    db.session.commit()

    return jsonify({
        'message': 'Product updated successfully',
        'product': {
            'id': product.id,
            'title': product.title,
            'price': product.price,
            'cost': product.cost,
            'stock': product.stock,
            'description': product.description,
            'image': product.image,
            'category': product.category.name if product.category else None
        }
    }), 200

@app.delete('/admin/product/delete/<int:id>')
@jwt_required()
def delete_product_by_id(id):

    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    product = Product.query.get(id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if product.image:
        old_filename = product.image.split('/uploads/')[-1]
        old_path = os.path.join(UPLOAD_FOLDER, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    db.session.delete(product)
    db.session.commit()

    return jsonify({'message': 'Product deleted successfully'}), 200

@app.delete('/admin/product/delete')
@jwt_required()
def delete_product():

    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    product_id = request.form.get('id') or request.json.get('id')
    if not product_id:
        return jsonify({'message': 'Product ID is required'}), 400

    try:
        product_id = int(product_id)
    except ValueError:
        return jsonify({'message': 'Product ID must be an integer'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if product.image:
        old_filename = product.image.split('/uploads/')[-1]
        old_path = os.path.join(UPLOAD_FOLDER, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    db.session.delete(product)
    db.session.commit()

    return jsonify({'message': 'Product deleted successfully'}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)\


@app.get('/admin/product/list')
@jwt_required()
def admin_get_products():
    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    products = Product.query.all()

    product_list = []
    for p in products:
        image_url = get_image_url(p.image)

        product_list.append({
    'id': p.id,
    'title': p.title,
    'price': p.price,
    'stock': p.stock,
    'description': p.description,
    'cost': p.cost,
    'category': p.category.name,
    'image': image_url
})


    return jsonify(product_list)




# Front Panel
@app.get('/product/list')
def get_products():
    products = Product.query.all()

    product_list = []
    for p in products:
        image_url = None
        if p.image:
            if p.image.startswith("http"):
                image_url = p.image
            else:
                image_url = request.host_url.rstrip('/') + p.image

        product_list.append({
            'id': p.id,
            'title': p.title,
            'price': p.price,
            'stock': p.stock,
            'description': p.description,
            'cost': p.cost,
            'category': p.category.name,
            'image': image_url

        })

    return jsonify(product_list)

@app.get('/product/list/category')
def get_products_by_category_name():
    data = request.get_json()

    category_name = data.get('category_name') if data else None
    if not category_name:
        return {"message": "category_name is required"}, 400

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        return {
            "message": "Category not found",
        }, 404

    products = (
        Product.query
        .join(Category)
        .filter(Category.name == category_name)
        .all()
    )

    if not products:
        return {
            "message": "No products found in this category",
        }, 200

    product_list = []
    for p in products:
        image_url = get_image_url(p.image)

        product_list.append({
            'id': p.id,
            'title': p.title,
            'price': p.price,
            'stock': p.stock,
            'description': p.description,
            'category': p.category.name,
            'image': image_url,
            'cost': p.cost
        })

    return jsonify(product_list), 200


