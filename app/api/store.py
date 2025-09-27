"""
Store API endpoints
"""

from flask import Blueprint, request, jsonify, Response
from bson import json_util
from bson.objectid import ObjectId
from app import mongo
from app.utils.decorators import admin_required
from app.utils.validators import validate_email
from app.services.cloudinary_service import CloudinaryService
import os
import stripe
from datetime import datetime, timezone
import traceback
from pymongo import ReturnDocument

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
    
    # Expect image to be an already uploaded Cloudinary URL (modern flow)
    if not isinstance(image, str) or not image.startswith("http"):
        return jsonify({"error": "Image must be a Cloudinary URL"}), 400
    image_url = image
    
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
        
        # Handle image update (only accept Cloudinary URL)
        image_url = image_data
        if image_url and (not isinstance(image_url, str) or not image_url.startswith("http")):
            return jsonify({"error": "Image must be a Cloudinary URL"}), 400
        
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
        print("[checkout] Missing STRIPE_SECRET_KEY")
        return jsonify({"error": "Stripe not configured"}), 500

    try:
        data = request.get_json(force=True) or {}
        items = data.get("items", [])
        currency = (data.get("currency") or "eur").lower()
        print("[checkout] origin=", request.headers.get("Origin"), "currency=", currency, "items_len=", len(items))
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"error": "items array required"}), 400

        line_items = []
        for item in items:
            qty = int(item.get("quantity", 1))
            if qty <= 0:
                return jsonify({"error": "invalid quantity"}), 400

            product_id = item.get("productId") or item.get("product_id")
            if product_id:
                # Precio seguro: leer de la base de datos
                try:
                    doc = mongo.store_items.find_one({"_id": ObjectId(product_id)})
                except Exception:
                    return jsonify({"error": f"invalid productId: {product_id}"}), 400
                if not doc:
                    return jsonify({"error": f"product not found: {product_id}"}), 404
                name = doc.get("name") or "Item"
                price = doc.get("price")
                # En nuestra base, price ya está en minor units (céntimos) → NO volver a multiplicar
                try:
                    unit_amount = int(round(float(price)))
                except Exception:
                    return jsonify({"error": f"invalid price for product: {product_id}"}), 400
                if unit_amount < 0:
                    return jsonify({"error": "invalid price"}), 400
                print("[checkout] productId=", product_id, "name=", name, "unit_amount=", unit_amount, "qty=", qty)
                line_items.append({
                    "price_data": {
                        "currency": currency,
                        "product_data": {"name": name},
                        "unit_amount": unit_amount,
                    },
                    "quantity": qty,
                })
            else:
                # Compatibilidad: usar nombre/precio del cliente (menos seguro)
                name = item.get("name")
                price = item.get("price")
                if not name or price is None:
                    return jsonify({"error": "each item requires productId or name+price"}), 400
                unit_amount = int(round(float(price) * 100))
                if unit_amount < 0:
                    return jsonify({"error": "invalid price"}), 400
                line_items.append({
                    "price_data": {
                        "currency": currency,
                        "product_data": {"name": name},
                        "unit_amount": unit_amount,
                    },
                    "quantity": qty,
                })

        # Success/cancel URLs from env or fallbacks
        # Success/cancel URL dinámicos basados en el origen permitido (mejor DX en dev/prod)
        req_origin = request.headers.get("Origin") or request.headers.get("origin") or ""
        allowed_origins = {
            "http://localhost:5173",
            "https://marina-ibarra.netlify.app",
        }
        if req_origin in allowed_origins:
            success_url = f"{req_origin}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{req_origin}/checkout/cancel"
        else:
            success_url = os.getenv("STRIPE_SUCCESS_URL", "http://localhost:5173/checkout/success")
            cancel_url = os.getenv("STRIPE_CANCEL_URL", "http://localhost:5173/checkout/cancel")
            if "CHECKOUT_SESSION_ID" not in success_url:
                sep = "&" if ("?" in success_url) else "?"
                success_url = f"{success_url}{sep}session_id={{CHECKOUT_SESSION_ID}}"

        print("[checkout] success_url=", success_url, "cancel_url=", cancel_url)
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            billing_address_collection="auto",
            shipping_address_collection={
                "allowed_countries": ["ES", "PT", "FR", "IT", "DE", "GB"]
            },
            phone_number_collection={"enabled": True},
            customer_creation="always",
            allow_promotion_codes=False,
        )
        print("[checkout] session_id=", session.id)
        return jsonify({"id": session.id, "url": session.url}), 200

    except Exception as e:
        print("[checkout][error]", str(e))
        print(traceback.format_exc())
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
    if not event:
        return jsonify({"error": "No event"}), 400

    if event.type == "checkout.session.completed":
        try:
            session = event.data.object
            session_id = session.get("id")
            currency = (session.get("currency") or "eur").lower()
            customer_details = session.get("customer_details") or {}
            customer_email = customer_details.get("email")
            customer_phone = customer_details.get("phone")
            shipping = session.get("shipping") or session.get("shipping_details") or {}
            shipping_name = shipping.get("name") if isinstance(shipping, dict) else None
            shipping_address = None
            addr = shipping.get("address") if isinstance(shipping, dict) else None
            if isinstance(addr, dict):
                shipping_address = {
                    "line1": addr.get("line1"),
                    "line2": addr.get("line2"),
                    "city": addr.get("city"),
                    "state": addr.get("state"),
                    "postal_code": addr.get("postal_code"),
                    "country": addr.get("country"),
                }

            # Alert/log if Stripe didn't provide an email (shouldn't happen in normal flow)
            if not customer_email:
                try:
                    mongo.alerts.insert_one({
                        "type": "missing_customer_email",
                        "session_id": session_id,
                        "raw_event_type": event.type,
                        "customer_details": customer_details,
                        "created_at": datetime.now(timezone.utc),
                    })
                except Exception as _e:
                    print(f"[webhook][warn] failed to record missing email alert: {_e}")
                print(f"[webhook][warn] missing customer_email for session {session_id}")

            # Retrieve line items to store order details
            line_items = stripe.checkout.Session.list_line_items(session_id, limit=100)
            items = []
            total_minor = 0
            for li in line_items.auto_paging_iter():
                description = li.get("description") or (li.get("price") or {}).get("nickname") or "Item"
                quantity = li.get("quantity") or 1
                amount_total = li.get("amount_total") or (li.get("price") or {}).get("unit_amount", 0) * quantity
                total_minor += int(amount_total or 0)
                items.append({
                    "description": description,
                    "quantity": quantity,
                    "amount_total_minor": int(amount_total or 0),
                })

            # Generate friendly order number (atomic counter, reset per year)
            current_year = datetime.now(timezone.utc).year
            counter_key = f"orders_{current_year}"
            counter_doc = mongo.counters.find_one_and_update(
                {"_id": counter_key},
                {"$inc": {"seq": 1}, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            seq_num = int(counter_doc.get("seq", 1))
            order_number = f"PED-{current_year}-{seq_num:05d}"

            order_doc = {
                "session_id": session_id,
                "payment_status": session.get("payment_status"),
                "currency": currency,
                "amount_total_minor": total_minor,
                "order_number": order_number,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "shipping_name": shipping_name,
                "shipping_address": shipping_address,
                "items": items,
                "created_at": datetime.now(timezone.utc),
                "raw": {"type": event.type},
            }

            mongo.orders.insert_one(order_doc)
        except Exception as e:
            # Log but don't fail webhook acknowledgment
            print(f"Order save error: {str(e)}")

    elif event.type == "payment_intent.succeeded":
        # No-op: covered by checkout.session.completed for Checkout flow
        pass

    return jsonify({"received": True}), 200


@store_bp.route('/store/orders', methods=['GET'])
@admin_required
def list_orders():
    """List recent orders (admin only)
    Query params:
      - limit: max number of orders to return (default 20, max 100)
    """
    try:
        limit = int(request.args.get('limit', 20))
        limit = max(1, min(limit, 100))
    except Exception:
        limit = 20
    try:
        page = int(request.args.get('page', 1))
        page = max(1, page)
    except Exception:
        page = 1
    skip = (page - 1) * limit

    orders_cursor = mongo.orders.find().sort([("created_at", -1)]).skip(skip).limit(limit)
    return Response(json_util.dumps(list(orders_cursor)), mimetype="application/json")


@store_bp.route('/store/orders/by-session/<session_id>', methods=['GET'])
def get_order_by_session(session_id: str):
    """Obtener un pedido por session_id (público) para mostrar resumen en success.
    Devuelve 404 si no existe.
    """
    try:
        doc = mongo.orders.find_one({"session_id": session_id})
        if not doc:
            return jsonify({"error": "Order not found"}), 404
        return Response(json_util.dumps(doc), mimetype="application/json")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@store_bp.route('/store/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Subscribe an email to the newsletter/updates list (public).
    Body JSON: { "email": string, "source": string? }
    Upsert by email (case-insensitive). Returns 200 on success.
    """
    try:
        data = request.get_json(force=True) or {}
        raw_email = (data.get("email") or "").strip()
        if not raw_email:
            return jsonify({"error": "email required"}), 400
        if not validate_email(raw_email):
            return jsonify({"error": "invalid email"}), 400
        email = raw_email.lower()
        source = (data.get("source") or "").strip() or "api"

        now = datetime.now(timezone.utc)
        mongo.subscribers.update_one(
            {"email": email},
            {
                "$set": {
                    "email": email,
                    "consent": True,
                    "source": source,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
