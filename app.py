import os
from flask import (
    Flask,
    request,
    jsonify,
    Response,
    render_template,
    redirect,
    url_for,
    session,
)
from pymongo import MongoClient
from flask_pymongo import PyMongo
from bson import json_util
from bson.objectid import ObjectId
from flask_cors import CORS
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from config import DevelopmentConfig

load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)
app.config.from_object(DevelopmentConfig)


# secret key para la session
app.secret_key = app.config['SECRET_KEY']


# jwt
JWT_KEY = app.config['JWT_KEY']
jwt = JWTManager(app)


# Atlas connection
CONNECTION_STRING = app.config['MONGO_CLUSTER']

cluster = MongoClient(CONNECTION_STRING)

mongo = cluster["marina_db"]


# ---------------------------------------------------------------------------- #
#    Routes
# ---------------------------------------------------------------------------- #
@app.route("/")
def _app():
    return render_template("login.html")


# ---------------------------------------------------------------------------- #
#    Login from react
# ---------------------------------------------------------------------------- #
@app.route('/token', methods=["POST"])
def create_token():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    # Consulta la base de datos por el nombre de usuario y la contraseña
    if email != "test@test.com" or password != "test":
        return {"msg": "Wrong email or password"}, 401

    access_token = create_access_token(identity=email)
    response = {"access_token": access_token}
    return response


@app.after_request
def _after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "https://king-prawn-app-dr5rk.ondigitalocean.app"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Content-Type, Content-Length, Accept-Encoding, " \
                                                       "X-CSRF-Token, Authorization "
    return response


# ---------------------------------------------------------------------------- #
#    Login from flask
# ---------------------------------------------------------------------------- #
@app.route("/login", methods=["GET", "POST"])
def _login():
    if request.method == "POST":
        session["user"] = request.form["email"]
        session["password"] = request.form["password"]
        return redirect(url_for("portfolio_manager"))
    else:
        return "bad request"


@app.route("/logout")
def _logout():
    session.clear()
    return redirect(url_for("_app"))


# ---------------------------------------------------------------------------- #
#    If Login redirect to manager
# ---------------------------------------------------------------------------- #
@app.route("/manager")
def portfolio_manager():
    # Comparar el email y la contraseña del formulario con la base de datos

    if session["user"] == "marcel@ibm.com" and session["password"] == "abcd1234":
        users = mongo.users.find()
        return render_template("manager.html", users=users)
    else:
        return "You do not have permission to view this"


# ---------------------------------------------------------------------------- #
#    Create users
# ---------------------------------------------------------------------------- #
@app.route("/users", methods=["POST"])
def create_user():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    if username and email and password:
        hashed_password = generate_password_hash(password)
        id = mongo.users.insert_one(
            {"username": username, "email": email, "password": hashed_password}
        )
        response = jsonify(
            {"_id": str(id), "username": username, "password": password, "email": email}
        )
        response.status_code = 201
        return redirect(url_for("portfolio_manager"))
    else:
        return "not_found"


# ---------------------------------------------------------------------------- #
#    Get all users
# ---------------------------------------------------------------------------- #
@app.route("/users", methods=["GET"])
def get_users():
    users = mongo.users.find()
    response = json_util.dumps(users)
    return Response(response, mimetype="application/json")


# ---------------------------------------------------------------------------- #
#    Get one user
# ---------------------------------------------------------------------------- #
@app.route("/users/<id>", methods=["GET"])
def get_one_user(id):
    user = mongo.users.find_one({"_id": ObjectId(id)})
    response = json_util.dumps(user)
    return Response(response, mimetype="application/json")


# ---------------------------------------------------------------------------- #
#    Delete one user
# ---------------------------------------------------------------------------- #
@app.route("/delete/<id>", methods=["DELETE", "GET"])
def delete(id):
    mongo.users.delete_one({"_id": ObjectId(id)})
    response = jsonify({"message": "User" + id + " Deleted Successfully"})
    response.status_code = 200
    return redirect(url_for("portfolio_manager"))


# ---------------------------------------------------------------------------- #
#    Update one user
# ---------------------------------------------------------------------------- #
@app.route("/update/<id>", methods=["POST", "GET"])
def update(id):
    user = mongo.users.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        mongo.users.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "username": request.form["username"],
                    "email": request.form["email"],
                    "password": request.form["password"],
                }
            },
        )
        new_password = request.form["password"]
        hashed_password = generate_password_hash(new_password)
        mongo.users.update_one(
            {"_id": ObjectId(id)}, {"$set": {"password": hashed_password}}
        )

        return redirect(url_for("portfolio_manager"))

    # Redirect to update one user form
    return render_template("update.html", user=user)


# ---------------------------------------------------------------------------- #
#    Add Porfolio items
# ---------------------------------------------------------------------------- #
@app.route("/add", methods=["POST"])
def add_portfolio_item():
    # Getting Input from (Postman) in JSON format
    jsonvalue = request.json
    # Picking the data from Variable
    name = jsonvalue["name"]
    description = jsonvalue["description"]
    thumb_img_url = jsonvalue["thumb_img_url"]
    gallery = jsonvalue["gallery"]

    # Obteniendo los datos desde React
    if name and description and thumb_img_url and gallery and request.method == "POST":
        id = mongo.portfolio_items.insert_one(
            {
                "name": name,
                "description": description,
                "thumb_img_url": thumb_img_url,
                "gallery": gallery,
            }
        )
        response = jsonify(
            {
                "_id": str(id),
                "name": name,
                "thumb_img_url": thumb_img_url,
                "description": description,
                "gallery": gallery,
            }
        )
        response.status_code = 201
        return response
    else:
        return "not_found"


# ---------------------------------------------------------------------------- #
#    Get all portfolio items
# ---------------------------------------------------------------------------- #
@app.route("/portfolio", methods=["GET"])
def get_portfolio_items():
    portfolio_items = mongo.portfolio_items.find()
    response = json_util.dumps(portfolio_items)
    return Response(response, mimetype="application/json")


# ---------------------------------------------------------------------------- #
#    Get one portfolio item
# ---------------------------------------------------------------------------- #
@app.route("/portfolio/<id>", methods=["GET"])
def get_portfolio_item(id):
    portfolio_item = mongo.portfolio_items.find_one({"_id": ObjectId(id)})
    response = json_util.dumps(portfolio_item)
    return Response(response, mimetype="application/json")


# ---------------------------------------------------------------------------- #
#    Delete one portfolio item
# ---------------------------------------------------------------------------- #
@app.route("/portfolio/<id>", methods=["DELETE"])
def delete_portfolio_item(id):
    mongo.portfolio_items.delete_one({"_id": ObjectId(id)})
    response = jsonify({"message": "Portfolio item" + id + " Deleted Successfully"})
    response.status_code = 200
    return Response(response, mimetype="application/json")


# ---------------------------------------------------------------------------- #
#   Add items to store
# ---------------------------------------------------------------------------- #
@app.route("/store", methods=["POST"])
def add_store_item():
    # Getting Input from (Postman) in JSON format
    jsonvalue = request.json
    # Picking the data from Variable
    name = jsonvalue["name"]
    price = jsonvalue["price"]
    description = jsonvalue["description"]
    image = jsonvalue["image"]

    # Obteniendo los datos desde React
    if name and price and description and image and request.method == "POST":
        id = mongo.store_items.insert_one(
            {
                "name": name,
                "price": price,
                "description": description,
                "image": image,
            }
        )
        response = jsonify(
            {
                "_id": str(id),
                "name": name,
                "price": price,
                "description": description,
                "image": image,
            }
        )
        response.status_code = 201
        return response
    else:
        return "not_found"


# ---------------------------------------------------------------------------- #
#    Get all store items
# ---------------------------------------------------------------------------- #
@app.route("/store", methods=["GET"])
def get_store_items():
    store_items = mongo.store_items.find()
    response = json_util.dumps(store_items)
    return Response(response, mimetype="application/json")


# ---------------------------------------------------------------------------- #
#    Get one store item
# ---------------------------------------------------------------------------- #
@app.route("/store/<id>", methods=["GET"])
def get_one_store_item(id):
    store_item = mongo.store_items.find_one({"_id": ObjectId(id)})
    response = json_util.dumps(store_item)
    return Response(response, mimetype="application/json")


# ---------------------------------------------------------------------------- #
#    Delete one store item
# ---------------------------------------------------------------------------- #
@app.route("/store/<id>", methods=["DELETE"])
def delete_one_store_item(id):
    mongo.store_items.delete_one({"_id": ObjectId(id)})
    response = jsonify({"message": "Store item" + id + " Deleted Successfully"})
    response.status_code = 200
    return Response(response, mimetype="application/json")


# ---------------------------------------------------------------------------- #
#
# ---------------------------------------------------------------------------- #
@app.errorhandler(404)
def not_found(error=None):
    message = {"message": "Resource Not Found " + request.url, "status": 404}
    response = jsonify(message)
    response.status_code = 404
    return response


if __name__ == "__main__":
    app.run()
