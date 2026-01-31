import json

from flask import request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import app, db
from model import Product, Category

# =====================================================
# IMAGE HELPER (URL ONLY)
# =====================================================

def get_image_url(image):
    if not image:
        return None

    if image.startswith("http"):
        return image

    image = image.replace("http://127.0.0.1:5000/uploads/", "")
    image = image.replace("http://localhost:5000/uploads/", "")
    image = image.replace("static/uploads/", "")
    image = image.replace("/uploads/", "")
    image = image.replace("uploads/", "")

    return url_for(
        "static",
        filename=f"uploads/{image}",
        _external=True
    )


# =====================================================
# AUTH HELPERS
# =====================================================

def require_admin():
    user = json.loads(get_jwt_identity())
    if user.get("role") != "admin":
        return None, (jsonify({"message": "Admin access required"}), 403)
    return user, None


def serialize_product(p):
    return {
        "id": p.id,
        "title": p.title,
        "price": p.price,
        "cost": p.cost,
        "stock": p.stock,
        "description": p.description,
        "category": p.category.name if p.category else None,
        "category_id": p.category_id,
        "image": get_image_url(p.image),
    }


# =====================================================
# ADMIN ROUTES
# =====================================================

@app.post("/admin/product/create")
@jwt_required()
def create_product():
    _, error = require_admin()
    if error:
        return error

    title = request.form.get("title", "").strip()
    price = request.form.get("price")
    cost = request.form.get("cost")
    stock = request.form.get("stock")
    category_id = request.form.get("category_id")
    description = request.form.get("description")
    image_url = request.form.get("image_url")  # ✅ URL ONLY

    if not all([title, price, cost, stock, category_id]):
        return jsonify({"message": "Missing required fields"}), 400

    if Product.query.filter_by(title=title).first():
        return jsonify({"message": "Product already exists"}), 400

    try:
        price = float(price)
        cost = float(cost)
        stock = int(stock)
        category_id = int(category_id)
    except ValueError:
        return jsonify({"message": "Invalid numeric values"}), 400

    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404

    product = Product(
        title=title,
        price=price,
        cost=cost,
        stock=stock,
        description=description,
        image=image_url,
        category_id=category_id,
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({
        "message": "Product created successfully",
        "product": serialize_product(product),
    }), 201


@app.put("/admin/product/update/<int:id>")
@jwt_required()
def update_product(id):
    _, error = require_admin()
    if error:
        return error

    product = Product.query.get(id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    title = request.form.get("title")
    price = request.form.get("price")
    cost = request.form.get("cost")
    stock = request.form.get("stock")
    category_id = request.form.get("category_id")
    description = request.form.get("description")
    image_url = request.form.get("image_url")

    if title:
        title = title.strip()
        exists = Product.query.filter(
            Product.title == title,
            Product.id != id
        ).first()
        if exists:
            return jsonify({"message": "Product title already exists"}), 400
        product.title = title

    try:
        if price is not None:
            product.price = float(price)
        if cost is not None:
            product.cost = float(cost)
        if stock is not None:
            product.stock = int(stock)
        if category_id is not None:
            category_id = int(category_id)
            if not Category.query.get(category_id):
                return jsonify({"message": "Category not found"}), 404
            product.category_id = category_id
    except ValueError:
        return jsonify({"message": "Invalid numeric values"}), 400

    if description is not None:
        product.description = description

    if image_url is not None:
        product.image = image_url

    db.session.commit()

    return jsonify({
        "message": "Product updated successfully",
        "product": serialize_product(product),
    }), 200


@app.delete("/admin/product/delete/<int:id>")
@jwt_required()
def delete_product(id):
    _, error = require_admin()
    if error:
        return error

    product = Product.query.get(id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product deleted successfully"}), 200


@app.get("/admin/product/list")
@jwt_required()
def admin_product_list():
    _, error = require_admin()
    if error:
        return error

    products = Product.query.all()
    return jsonify({
        "total": len(products),
        "products": [serialize_product(p) for p in products],
    }), 200


# =====================================================
# PUBLIC ROUTES
# =====================================================

@app.get("/product/list")
def product_list():
    products = Product.query.all()
    return jsonify({
        "total": len(products),
        "products": [serialize_product(p) for p in products],
    }), 200


@app.get("/product/<int:id>")
def product_detail(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    return jsonify({"product": serialize_product(product)}), 200


@app.get("/product/category/<int:category_id>")
def product_by_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404

    products = Product.query.filter_by(category_id=category_id).all()

    return jsonify({
        "category": category.name,
        "total": len(products),
        "products": [serialize_product(p) for p in products],
    }), 200
