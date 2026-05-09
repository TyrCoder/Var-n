"""
SQLAlchemy Database Models for Varon E-Commerce Platform
Migrated from raw SQL to ORM for better maintainability and connection pooling
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func, Index
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

db = SQLAlchemy()

# Define ENUM types
user_role_enum = PG_ENUM('buyer', 'seller', 'admin', 'rider', name='user_role')
user_status_enum = PG_ENUM('active', 'inactive', 'pending', 'suspended', name='user_status')
seller_status_enum = PG_ENUM('pending', 'approved', 'rejected', 'suspended', name='seller_status')
product_gender_enum = PG_ENUM('men', 'women', 'unisex', name='product_gender')
edit_status_enum = PG_ENUM('none', 'pending', 'approved', 'rejected', name='edit_status')
archive_status_enum = PG_ENUM('active', 'archived', 'pending_recovery', name='archive_status')
payment_status_enum = PG_ENUM('pending', 'paid', 'failed', 'refunded', name='payment_status')
order_status_enum = PG_ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned', name='order_status')
address_type_enum = PG_ENUM('billing', 'shipping', 'both', name='address_type')
vehicle_type_enum = PG_ENUM('motorcycle', 'bicycle', 'car', 'van', 'truck', name='vehicle_type')
rider_status_enum = PG_ENUM('available', 'on_delivery', 'on_break', 'offline', name='rider_status')
shipment_status_enum = PG_ENUM('pending', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned', name='shipment_status')
review_status_enum = PG_ENUM('pending', 'approved', 'rejected', name='review_status')


class User(db.Model):
    """User table for customers, sellers, admins, riders"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(190), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(user_role_enum, default='buyer', nullable=False, index=True)
    phone = db.Column(db.String(20))
    status = db.Column(user_status_enum, default='active', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = db.relationship('Seller', uselist=False, back_populates='user', cascade='all, delete-orphan')
    rider = db.relationship('Rider', uselist=False, back_populates='user', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='user', cascade='all, delete-orphan')
    addresses = db.relationship('Address', back_populates='user', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='user', cascade='all, delete-orphan')


class Category(db.Model):
    """Product categories (hierarchical)"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), index=True)
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', back_populates='category')
    subcategories = db.relationship('Category', remote_side=[id], cascade='all, delete-orphan')


class Seller(db.Model):
    """Seller profiles and store information"""
    __tablename__ = 'sellers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    store_name = db.Column(db.String(150), nullable=False)
    store_slug = db.Column(db.String(150), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    business_license = db.Column(db.String(100))
    tax_id = db.Column(db.String(100))
    bank_account = db.Column(db.String(100))
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_sales = db.Column(db.Numeric(15, 2), default=0.00)
    commission_rate = db.Column(db.Numeric(5, 2), default=10.00)
    status = db.Column(seller_status_enum, default='pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='seller')
    products = db.relationship('Product', back_populates='seller', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='seller')


class Product(db.Model):
    """Product listings"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    brand = db.Column(db.String(100))
    gender = db.Column(product_gender_enum, default='men')
    price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2))
    cost_price = db.Column(db.Numeric(10, 2))
    sku = db.Column(db.String(100), unique=True)
    weight = db.Column(db.Numeric(8, 2))
    dimensions = db.Column(db.String(100))
    material = db.Column(db.String(200))
    care_instructions = db.Column(db.Text)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    views_count = db.Column(db.Integer, default=0)
    sales_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    review_count = db.Column(db.Integer, default=0)
    edit_status = db.Column(edit_status_enum, default='none', index=True)
    archive_status = db.Column(archive_status_enum, default='active', index=True)
    archived_at = db.Column(db.DateTime)
    archived_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = db.relationship('Seller', back_populates='products')
    category = db.relationship('Category', back_populates='products')
    images = db.relationship('ProductImage', back_populates='product', cascade='all, delete-orphan')
    variants = db.relationship('ProductVariant', back_populates='product', cascade='all, delete-orphan')
    inventory = db.relationship('Inventory', back_populates='product', uselist=False, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', back_populates='product')
    reviews = db.relationship('Review', back_populates='product', cascade='all, delete-orphan')


class ProductImage(db.Model):
    """Product images/photos"""
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', back_populates='images')


class ProductVariant(db.Model):
    """Product variants (size, color)"""
    __tablename__ = 'product_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    sku = db.Column(db.String(100), unique=True)
    size = db.Column(db.String(20))
    color = db.Column(db.String(50))
    stock_quantity = db.Column(db.Integer, default=0)
    price_adjustment = db.Column(db.Numeric(10, 2), default=0.00)
    weight_adjustment = db.Column(db.Numeric(8, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', back_populates='variants')
    inventory = db.relationship('Inventory', back_populates='variant', uselist=False, cascade='all, delete-orphan')


class Inventory(db.Model):
    """Inventory tracking"""
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='CASCADE'))
    stock_quantity = db.Column(db.Integer, default=0)
    reserved_quantity = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=10)
    reorder_point = db.Column(db.Integer, default=5)
    last_restocked_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', back_populates='inventory')
    variant = db.relationship('ProductVariant', back_populates='inventory')


class Address(db.Model):
    """Customer addresses"""
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    address_type = db.Column(address_type_enum, default='shipping')
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    street_address = db.Column(db.Text, nullable=False)
    barangay = db.Column(db.String(100))
    city = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50), default='Philippines')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='addresses')


class Order(db.Model):
    """Orders"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id', ondelete='RESTRICT'), nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id', ondelete='RESTRICT'), nullable=False)
    billing_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id', ondelete='RESTRICT'))
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_fee = db.Column(db.Numeric(10, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.00)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(payment_status_enum, default='pending')
    order_status = db.Column(order_status_enum, default='pending', index=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='orders')
    seller = db.relationship('Seller', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')


class OrderItem(db.Model):
    """Items in an order"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='RESTRICT'))
    product_name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100))
    size = db.Column(db.String(20))
    color = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product', back_populates='order_items')


class Rider(db.Model):
    """Rider profiles"""
    __tablename__ = 'riders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    vehicle_type = db.Column(vehicle_type_enum, nullable=False)
    license_number = db.Column(db.String(50))
    vehicle_plate = db.Column(db.String(20))
    service_area = db.Column(db.Text)
    address_region_code = db.Column(db.String(20))
    address_region_name = db.Column(db.String(150))
    address_province_code = db.Column(db.String(20))
    address_province_name = db.Column(db.String(150))
    address_city_code = db.Column(db.String(20))
    address_city_name = db.Column(db.String(150))
    average_rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_deliveries = db.Column(db.Integer, default=0)
    current_status = db.Column(rider_status_enum, default='offline')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='rider')


class Shipment(db.Model):
    """Shipment tracking"""
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('riders.id', ondelete='SET NULL'))
    tracking_number = db.Column(db.String(100), unique=True)
    status = db.Column(shipment_status_enum, default='pending', index=True)
    estimated_delivery = db.Column(db.DateTime)
    actual_delivery = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Review(db.Model):
    """Product reviews and ratings"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    order_item_id = db.Column(db.Integer)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    status = db.Column(review_status_enum, default='pending')
    helpful_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')


class OTP(db.Model):
    """One-Time Password for email verification"""
    __tablename__ = 'otp'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(190), nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(50), default='signup')
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)


class SellerNotification(db.Model):
    """Notifications for sellers"""
    __tablename__ = 'seller_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False, index=True)
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='SET NULL'))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
