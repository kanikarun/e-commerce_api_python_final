from app import db

class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))

    category_id = db.Column(
        db.Integer, db.ForeignKey("category.id"), nullable=False
    )

    carts = db.relationship("Cart", backref="product", lazy=True)
    order_details = db.relationship("OrderDetail", backref="product", lazy=True)
