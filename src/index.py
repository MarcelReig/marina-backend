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
from config import config

from werkzeug.security import generate_password_hash

app = Flask(__name__)
CORS(app)

# Atlas connection
cluster = MongoClient(
    "mongodb+srv://MarcelReig:Ml00TSOSq4CBTsMN@cluster0.5mwmz.mongodb.net/?retryWrites=true&w=majority"
)

mongo = cluster["marina_db"]

# secret key para la session
app.secret_key = "6+8zZ69dzChLZCU9h=XE+Gren}fnRV"


######################
####    Routes
#####################
@app.route("/")
def index():
    return render_template("login.html")


######################
####    Login
#####################
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        session["user"] = request.form["email"]
        session["password"] = request.form["password"]
        return redirect(url_for("portfolioManager"))
    else:
        return "bad request"


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#######################################
####    If Login redirect to manager
######################################
@app.route("/manager")
def portfolioManager():
    # Comparar el email y la contraseña del formulario con la base de datos

    if session["user"] == "marcel@ibm.com" and session["password"] == "abcd1234":
        users = mongo.users.find()
        return render_template("manager.html", users=users)
    else:
        return "You do not have permission to view this"


#######################################
####    Create users
######################################
@app.route("/users", methods=["POST"])
def createUser():
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
        return redirect(url_for("portfolioManager"))
    else:
        return "not_found"


#######################################
####    Get all users
######################################
@app.route("/users", methods=["GET"])
def getUsers():
    users = mongo.users.find()
    response = json_util.dumps(users)
    return Response(response, mimetype="application/json")


#######################################
####    Get one user
######################################
@app.route("/users/<id>", methods=["GET"])
def getUser(id):
    user = mongo.users.find_one({"_id": ObjectId(id)})
    response = json_util.dumps(user)
    return Response(response, mimetype="application/json")


#######################################
####    Delete one user
######################################
@app.route("/delete/<id>", methods=["DELETE", "GET"])
def delete(id):
    mongo.users.delete_one({"_id": ObjectId(id)})
    response = jsonify({"message": "User" + id + " Deleted Successfully"})
    response.status_code = 200
    return redirect(url_for("portfolioManager"))


#######################################
####    Update one user
######################################
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
        newPassword = request.form["password"]
        hashed_password = generate_password_hash(newPassword)
        mongo.users.update_one(
            {"_id": ObjectId(id)}, {"$set": {"password": hashed_password}}
        )

        return redirect(url_for("portfolioManager"))

    # Redirect to update one user form
    return render_template("update.html", user=user)


#######################################
####    Add Porfolio items
######################################
@app.route("/add", methods=["POST"])
def addPortfolioItem():
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


#######################################
####    Get all portfolio items
######################################
@app.route("/portfolio", methods=["GET"])
def getPortfolioItems():
    portfolioItems = mongo.portfolio_items.find()
    response = json_util.dumps(portfolioItems)
    return Response(response, mimetype="application/json")


#######################################
####    Get one portfolio item
######################################
@app.route("/portfolio/<id>", methods=["GET"])
def getPortfolioItem(id):
    portfolioItem = mongo.portfolio_items.find_one({"_id": ObjectId(id)})
    response = json_util.dumps(portfolioItem)
    return Response(response, mimetype="application/json")


#######################################
####    Delete one portfolio item
######################################
@app.route("/portfolio/<id>", methods=["DELETE"])
def deletePfolioItem(id):
    mongo.portfolio_items.delete_one({"_id": ObjectId(id)})
    response = jsonify({"message": "Portfolio item" + id + " Deleted Successfully"})
    response.status_code = 200
    return Response(response, mimetype="application/json")


#######################################
####    Add items to store
######################################
@app.route("/store", methods=["POST"])
def addStoreItem():
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

#######################################
####    Get all store items
######################################
@app.route("/store", methods=["GET"])
def getStoreItems():
    storeItems = mongo.store_items.find()
    response = json_util.dumps(storeItems)
    return Response(response, mimetype="application/json")

#######################################
####    Get one store item
######################################
@app.route("/store/<id>", methods=["GET"])
def getStoreItem(id):
    storeItem = mongo.store_items.find_one({"_id": ObjectId(id)})
    response = json_util.dumps(storeItem)
    return Response(response, mimetype="application/json")


#######################################
####    Delete one store item
######################################
@app.route("/store/<id>", methods=["DELETE"])
def deleteStoreItem(id):
    mongo.store_items.delete_one({"_id": ObjectId(id)})
    response = jsonify({"message": "Store item" + id + " Deleted Successfully"})
    response.status_code = 200
    return Response(response, mimetype="application/json")


#######################################
####
######################################

@app.errorhandler(404)
def not_found(error=None):
    message = {"message": "Resource Not Found " + request.url, "status": 404}
    response = jsonify(message)
    response.status_code = 404
    return response


if __name__ == "__main__":
    app.config.from_object(config["development"])
    app.run()
