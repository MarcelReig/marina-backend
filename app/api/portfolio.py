"""
Portfolio API endpoints
"""

from flask import Blueprint, request, jsonify, Response
from bson import json_util
from bson.objectid import ObjectId
from app import mongo
from app.utils.decorators import admin_required
from app.services.cloudinary_service import CloudinaryService

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/portfolio', methods=['GET'])
def get_portfolio_items():
    """Get all portfolio items (public endpoint)"""
    portfolio_items = mongo.portfolio_items.find()
    response = json_util.dumps(portfolio_items)
    return Response(response, mimetype="application/json")


@portfolio_bp.route('/portfolio/<id>', methods=['GET'])
def get_portfolio_item(id):
    """Get single portfolio item (public endpoint)"""
    try:
        portfolio_item = mongo.portfolio_items.find_one({"_id": ObjectId(id)})
        if not portfolio_item:
            return jsonify({"error": "Portfolio item not found"}), 404
        
        response = json_util.dumps(portfolio_item)
        return Response(response, mimetype="application/json")
    except Exception as e:
        return jsonify({"error": "Invalid portfolio ID"}), 400


@portfolio_bp.route('/portfolio/<id>', methods=['PUT'])
@admin_required
def update_portfolio_item(id):
    """Update existing portfolio item (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400
        
        # Extract required fields
        name = data.get("name")
        description = data.get("description")
        thumb_img_data = data.get("thumb_img_url")
        gallery_data = data.get("gallery")
        
        if not all([name, description, thumb_img_data, gallery_data]):
            return jsonify({"error": "Missing required fields: name, description, thumb_img_url, gallery"}), 400
        
        # Only upload to Cloudinary if it's base64 data (new images)
        if thumb_img_data.startswith('data:image'):
            thumb_url, _, error = CloudinaryService.upload_portfolio_images(thumb_img_data, [])
            if error:
                return jsonify({"error": error}), 500
        else:
            thumb_url = thumb_img_data  # Keep existing URL
            
        # Process gallery images
        gallery_urls = []
        for img_data in gallery_data:
            if isinstance(img_data, str) and img_data.startswith('data:image'):
                # New image - upload to Cloudinary
                img_url = CloudinaryService.upload_image(img_data, "portfolio/gallery")
                if img_url:
                    gallery_urls.append(img_url)
                else:
                    return jsonify({"error": "Failed to upload gallery image"}), 500
            else:
                # Existing URL - keep it
                gallery_urls.append(img_data)
        
        # Update in database
        result = mongo.portfolio_items.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "name": name,
                "description": description,
                "thumb_img_url": thumb_url,
                "gallery": gallery_urls,
            }}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Portfolio item not found"}), 404
        
        response = {
            "_id": id,
            "name": name,
            "thumb_img_url": thumb_url,
            "description": description,
            "gallery": gallery_urls,
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": "Database error"}), 500


@portfolio_bp.route('/portfolio', methods=['POST'])
@admin_required
def add_portfolio_item():
    """Create new portfolio item (admin only)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    # Extract required fields
    name = data.get("name")
    description = data.get("description")
    thumb_img_data = data.get("thumb_img_url")
    gallery_data = data.get("gallery")
    
    if not all([name, description, thumb_img_data, gallery_data]):
        return jsonify({"error": "Missing required fields: name, description, thumb_img_url, gallery"}), 400
    
    # Upload images to Cloudinary
    thumb_url, gallery_urls, error = CloudinaryService.upload_portfolio_images(
        thumb_img_data, gallery_data
    )
    
    if error:
        return jsonify({"error": error}), 500
    
    # Save to database
    try:
        result = mongo.portfolio_items.insert_one({
            "name": name,
            "description": description,
            "thumb_img_url": thumb_url,
            "gallery": gallery_urls,
        })
        
        response = {
            "_id": str(result.inserted_id),
            "name": name,
            "thumb_img_url": thumb_url,
            "description": description,
            "gallery": gallery_urls,
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        return jsonify({"error": "Database error"}), 500


@portfolio_bp.route('/portfolio/<id>', methods=['DELETE'])
@admin_required
def delete_portfolio_item(id):
    """Delete portfolio item (admin only)"""
    try:
        result = mongo.portfolio_items.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 1:
            return jsonify({"message": f"Portfolio item {id} deleted successfully"}), 200
        else:
            return jsonify({"error": "Portfolio item not found"}), 404
    except Exception as e:
        return jsonify({"error": "Invalid portfolio ID"}), 400


@portfolio_bp.route('/portfolio/clear-all', methods=['DELETE'])
@admin_required
def clear_all_portfolio_items():
    """Delete all portfolio items (admin only - temporary cleanup)"""
    try:
        result = mongo.portfolio_items.delete_many({})
        return jsonify({
            "message": f"Deleted {result.deleted_count} portfolio items successfully",
            "deleted_count": result.deleted_count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
