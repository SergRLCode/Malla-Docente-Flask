# -*- coding: utf-8 -*-

from flask_jwt_extended import JWTManager
from flask_mongoengine import MongoEngine
from flask_cors import CORS
from flask import Flask
import redis

app = Flask(__name__)
app.config['MONGODB_DB'] = 'Capacitacion'
app.config['JWT_SECRET_KEY'] = 'uCm3uZm1kGPlB7ATTlsMoA'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

redis = redis.Redis(host='localhost', port=6379)
db = MongoEngine(app)
jwt = JWTManager(app)
CORS(app)

from routes import *

if __name__ == '__main__':
   app.run(debug=True)
