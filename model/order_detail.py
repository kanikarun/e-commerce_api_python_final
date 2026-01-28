from app import db

class OrderDetail(db.Model):
    __tablename__ = "order_detail"

    id = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)

    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id"), nullable=False
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id"), nullable=False
    )
