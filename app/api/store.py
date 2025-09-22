"""
Store API endpoints
"""

from flask import Blueprint, request, jsonify, Response
from bson import json_util
from bson.objectid import ObjectId
from app import mongo
from app.utils.decorators import admin_required
from app.services.cloudinary_service import CloudinaryService
import os
import stripe

store_bp = Blueprint('store', __name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


@store_bp.route('/store', methods=['GET'])
def get_store_items():
    """Get all store items (public endpoint)"""
    try:
        # Sort by display_order (ascending), then by _id for items without order
        store_items = list(mongo.store_items.find().sort([("display_order", 1), ("_id", 1)]))
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
    
    # Get next display_order (highest + 1)
    last_item = mongo.store_items.find().sort("display_order", -1).limit(1)
    next_order = 1
    for item in last_item:
        next_order = item.get("display_order", 0) + 1
        break
    
    # Save to database
    try:
        result = mongo.store_items.insert_one({
            "name": name,
            "price": price,
            "description": description,
            "image": image_url,
            "display_order": next_order,
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


@store_bp.route('/store/<id>', methods=['PUT'])
@admin_required
def update_store_item(id):
    """Update store item (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400
        
        # Extract required fields
        name = data.get("name")
        price = data.get("price")
        description = data.get("description")
        image_data = data.get("image")
        
        if not all([name, price, description]):
            return jsonify({"error": "Missing required fields: name, price, description"}), 400
        
        # Validate price
        try:
            price = float(price)
            if price < 0:
                return jsonify({"error": "Price must be positive"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid price format"}), 400
        
        # Handle image update
        if image_data and image_data.startswith('data:image'):
            # New image - upload to Cloudinary
            image_url, error = CloudinaryService.upload_store_image(image_data)
            if error:
                return jsonify({"error": error}), 500
        else:
            # Keep existing image URL
            image_url = image_data
        
        # Update in database
        result = mongo.store_items.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "name": name,
                "price": price,
                "description": description,
                "image": image_url,
            }}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Store item not found"}), 404
        
        response = {
            "_id": id,
            "name": name,
            "price": price,
            "description": description,
            "image": image_url,
        }
        
        return jsonify(response), 200
        
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


@store_bp.route('/store/reorder', methods=['PUT'])
@admin_required
def reorder_store_items():
    """Reorder store items (admin only)"""
    try:
        data = request.get_json()
        if not data or "items" not in data:
            return jsonify({"error": "Items array required"}), 400
        
        items = data["items"]
        if not isinstance(items, list):
            return jsonify({"error": "Items must be an array"}), 400
        
        # Update display_order for each item
        for index, item in enumerate(items):
            item_id = item.get("id")
            if not item_id:
                continue
                
            try:
                # Update the display_order field
                mongo.store_items.update_one(
                    {"_id": ObjectId(item_id)},
                    {"$set": {"display_order": index + 1}}
                )
            except Exception as e:
                print(f"Error updating item {item_id}: {str(e)}")
                continue
        
        return jsonify({"message": "Store order updated successfully"}), 200
        
    except Exception as e:
        print(f"Reorder error: {str(e)}")
        return jsonify({"error": "Failed to reorder store items"}), 500


@store_bp.route('/store/checkout/session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe Checkout Session for the current cart.
    Expects JSON: { items: [ { name, price, quantity } ] }
    price is a number in main currency units (e.g., 12.50)
    """
    if not stripe.api_key:
        return jsonify({"error": "Stripe not configured"}), 500

    try:
        data = request.get_json(force=True) or {}
        items = data.get("items", [])
        currency = (data.get("currency") or "eur").lower()
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"error": "items array required"}), 400

        line_items = []
        for item in items:
            name = item.get("name")
            price = item.get("price")
            qty = int(item.get("quantity", 1))
            if not name or price is None:
                return jsonify({"error": "each item requires name and price"}), 400
            # Convert to smallest currency unit (e.g., cents)
            unit_amount = int(round(float(price) * 100))
            if unit_amount < 0 or qty <= 0:
                return jsonify({"error": "invalid price or quantity"}), 400
            line_items.append({
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": name},
                    "unit_amount": unit_amount,
                },
                "quantity": qty,
            })

        # Success/cancel URLs from env or fallbacks
        success_url = os.getenv("STRIPE_SUCCESS_URL", "http://localhost:5173/?success=true")
        cancel_url = os.getenv("STRIPE_CANCEL_URL", "http://localhost:5173/?canceled=true")

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return jsonify({"id": session.id, "url": session.url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@store_bp.route('/store/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks.
    Configure STRIPE_WEBHOOK_SECRET and verify signature.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature', None)
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    event = None
    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=endpoint_secret
            )
        else:
            # No signature verification (dev only)
            event = stripe.Event.construct_from(request.get_json(force=True), stripe.api_key)
    except Exception as e:
        return jsonify({"error": f"Webhook error: {str(e)}"}), 400

    # Handle the event types you care about
    if event and event.type in ("checkout.session.completed", "payment_intent.succeeded"):
        # TODO: record order/fulfillment if needed
        pass

    return jsonify({"received": True}), 200
