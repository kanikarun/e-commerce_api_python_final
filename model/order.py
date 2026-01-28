from datetime import datetime

from app import db


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    paid_by = db.Column(db.String(128))
    status = db.Column(db.String(50), default="pending")

    customer_id = db.Column(
        db.Integer, db.ForeignKey("customer.id"), nullable=False
    )

    details = db.relationship("OrderDetail", backref="order", lazy=True)
