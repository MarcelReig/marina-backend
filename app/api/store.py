"""
Store API endpoints
"""

from flask import Blueprint, request, jsonify, Response
from bson import json_util
from bson.objectid import ObjectId
from app import mongo
from app.utils.decorators import admin_required
from app.services.cloudinary_service import CloudinaryService

store_bp = Blueprint('store', __name__)


@store_bp.route('/store', methods=['GET'])
def get_store_items():
    """Get all store items (public endpoint)"""
    try:
        store_items = list(mongo.store_items.find())
        # Convert ObjectId to string for JSON serialization
        for item in store_items:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        return jsonify(store_items), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch store items"}), 500


@store_bp.route('/store/<id>', methods=['GET'])
def get_store_item(id):
    """Get single store item (public endpoint)"""
    try:
        store_item = mongo.store_items.find_one({"_id": ObjectId(id)})
        if not store_item:
            return jsonify({"error": "Store item not found"}), 404
        
        # Convert ObjectId to string for JSON serialization
        store_item['_id'] = str(store_item['_id'])
        return jsonify(store_item), 200
    except Exception as e:
        return jsonify({"error": "Invalid store item ID"}), 400


@store_bp.route('/store', methods=['POST'])
@admin_required
def add_store_item():
    """Create new store item (admin only)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    # Extract required fields
    name = data.get("name")
    price = data.get("price")
    description = data.get("description")
    image = data.get("image")
    
    if not all([name, price, description, image]):
        return jsonify({"error": "Missing required fields: name, price, description, image"}), 400
    
    # Validate price
    try:
        price = float(price)
        if price < 0:
            return jsonify({"error": "Price must be positive"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid price format"}), 400
    
    # Upload image to Cloudinary
    image_url, error = CloudinaryService.upload_store_image(image)
    if error:
        return jsonify({"error": error}), 500
    
    # Save to database
    try:
        result = mongo.store_items.insert_one({
            "name": name,
            "price": price,
            "description": description,
            "image": image_url,
        })
        
        response = {
            "_id": str(result.inserted_id),
            "name": name,
            "price": price,
            "description": description,
            "image": image_url,
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        return jsonify({"error": "Database error"}), 500


@store_bp.route('/store/<id>', methods=['DELETE'])
@admin_required
def delete_store_item(id):
    """Delete store item (admin only)"""
    try:
        result = mongo.store_items.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 1:
            return jsonify({"message": f"Store item {id} deleted successfully"}), 200
        else:
            return jsonify({"error": "Store item not found"}), 404
    except Exception as e:
        return jsonify({"error": "Invalid store item ID"}), 400
