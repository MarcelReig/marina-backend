from flask import Flask, request, jsonify, Response, render_template, redirect, url_for, session
from flask_pymongo import PyMongo
from bson import json_util
from bson.objectid import ObjectId
from flask_cors import CORS
from config import config

from werkzeug.security import generate_password_hash

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = "mongodb://localhost/marinaDatabase"

mongo = PyMongo(app)

app.secret_key = '6+8zZ69dzChLZCU9h=XE+Gren}fnRV'

# Routes


@app.route("/")
def index():
    return render_template('login.html')


@app.route("/login", methods=["GET", "POST"])
def login():
   
    if request.method == "POST":
        session['user'] = request.form["email"]
        session['password'] = request.form["password"]
        return redirect(url_for("portfolioManager"))
    else:
        return "bad request"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/manager")
def portfolioManager():

    if session['user'] == "marcel@ibm.com" and session['password'] == "abcd1234":
        users = mongo.db.users.find()
        return render_template("manager.html", users=users)
    else:
        return "You do not have permission to view this"


@app.route("/users", methods=["POST"])
def createUser():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    if username and email and password:
        hashed_password = generate_password_hash(password)
        id = mongo.db.users.insert_one(
            {"username": username, "email": email, "password": hashed_password}
        )
        response = jsonify(
            {"_id": str(id), "username": username, "password": password, "email": email}
        )
        response.status_code = 201
        return redirect(url_for("portfolioManager"))
    else:
        return "not_found"


# Get all users
@app.route("/users", methods=["GET"])
def getUsers():
    users = mongo.db.users.find()
    response = json_util.dumps(users)
    return Response(response, mimetype="application/json")


# Get one user
@app.route("/users/<id>", methods=["GET"])
def getUser(id):
    user = mongo.db.users.find_one({"_id": ObjectId(id)})
    response = json_util.dumps(user)
    return Response(response, mimetype="application/json")


# Delete one user
@app.route("/delete/<id>", methods=["DELETE", "GET"])
def delete(id):
    mongo.db.users.delete_one({"_id": ObjectId(id)})
    response = jsonify({"message": "User" + id + " Deleted Successfully"})
    response.status_code = 200
    return redirect(url_for("portfolioManager"))


# Update one user
@app.route("/update/<id>", methods=["POST", "GET"])
def update(id):

    user = mongo.db.users.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        mongo.db.users.update_one(
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
        mongo.db.users.update_one(
            {"_id": ObjectId(id)}, {"$set": {"password": hashed_password}}
        )

        return redirect(url_for("portfolioManager"))

    # redirect to update one user form
    return render_template("update.html", user=user)


@app.errorhandler(404)
def not_found(error=None):
    message = {"message": "Resource Not Found " + request.url, "status": 404}
    response = jsonify(message)
    response.status_code = 404
    return response


if __name__ == "__main__":
    app.config.from_object(config["development"])
    app.run()
