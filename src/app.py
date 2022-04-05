from flask import Flask, request, jsonify, Response
from flask_pymongo import PyMongo
from bson import json_util
from bson.objectid import ObjectId
from flask_cors import CORS


from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = "mongodb://localhost/marinaDatabase"

mongo = PyMongo(app)

# Database
db = mongo.db.users

# Routes
@app.route('/')
def landingMsg():
  return '<h1>Enjoy Life</h1>'

@app.route('/users', methods=['POST'])
def createUser():
    # Receiving Data
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if username and email and password:
        hashed_password = generate_password_hash(password)
        id = mongo.db.users.insert_one(
            {'username': username, 'email': email, 'password': hashed_password})
        response = jsonify({
            '_id': str(id),
            'username': username,
            'password': password,
            'email': email
        })
        response.status_code = 201
        return response
    else:
        return not_found()

@app.route('/users', methods=['GET'])
def getUsers():
    users = mongo.db.users.find()
    response = json_util.dumps(users)
    return Response(response, mimetype="application/json")

@app.route('/users/<id>', methods=['GET'])
def getUser(id):
  user = mongo.db.users.find_one({'_id': ObjectId(id)})
  response = json_util.dumps(user)
  return Response(response, mimetype="application/json")

@app.route('/users/<id>', methods=['DELETE'])
def deleteUser(id):
  mongo.db.users.delete_one({'_id': ObjectId(id)})
  response = jsonify({'message': 'User' + id + ' Deleted Successfully'})
  response.status_code = 200
  return response

@app.route('/users/<_id>', methods=['PUT'])
def updateUser(_id):
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    if username and email and password and _id:
        hashed_password = generate_password_hash(password)
        mongo.db.users.update_one(
            {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, {'$set': {'username': username, 'email': email, 'password': hashed_password}})
        response = jsonify({'message': 'User' + _id + 'Updated Successfuly'})
        response.status_code = 200
        return response
    else:
      return not_found()

@app.errorhandler(404)
def not_found(error=None):
  message = {
      'message': 'Resource Not Found ' + request.url,
      'status': 404
  }
  response = jsonify(message)
  response.status_code = 404
  return response

if __name__ == "__main__":
  app.run(debug=True)
