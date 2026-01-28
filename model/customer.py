from app import db

class Customer(db.Model):
    __tablename__ = "customer"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password = db.Column(db.String(128))

    carts = db.relationship("Cart", backref="customer", lazy=True)
    orders = db.relationship("Order", backref="customer", lazy=True)