from app import db

class Cart(db.Model):
    __tablename__ = "cart"

    id = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer, nullable=False)

    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id"), nullable=False
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customer.id"), nullable=False
    )
