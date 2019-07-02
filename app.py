# -*- coding: utf-8 -*-

from flask_jwt_extended import JWTManager
from flask_mongoengine import MongoEngine
from flask_cors import CORS
from flask import Flask
import redis
import sys

app = Flask(__name__)
app.config['MONGODB_DB'] = 'Capacitacion'
app.config['JWT_SECRET_KEY'] = 'uCm3uZm1kGPlB7ATTlsMoA'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

redis = redis.StrictRedis(password='invierno')
db = MongoEngine(app)
jwt = JWTManager(app)
CORS(app)

from routes import *

message = """
Options and arguments:
-host    : IP of current server
-port    : Port el que quieras xd

Ejemplo: python3 file.py -host ip_address -port port_of_server
"""

if __name__ == '__main__':
    if len(sys.argv) != 3 and len(sys.argv) != 5:
        print(message)
        sys.exit()
    elif len(sys.argv) == 3:
        if(sys.argv[1] == '-host'):
            app.run(debug=True, host=sys.argv[2], port=5000)
        else:
            print(message)
    elif len(sys.argv) == 5:
        if(sys.argv[1] == '-host' and sys.argv[3] == '-port'):
            app.run(debug=True, host=sys.argv[2], port=sys.argv[4])
        else:
            print(message)
