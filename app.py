# -*- coding: utf-8 -*-

from flask_jwt_extended import JWTManager
from flask_mongoengine import MongoEngine
from flask_cors import CORS
from flask import Flask
import mongoengine
import redis
import sys

app = Flask(__name__)
mongoengine.connection.disconnect()
app.config['MONGODB_SETTINGS'] = {'db':'Capacitacion', 'alias':'default'}
app.config['JWT_SECRET_KEY'] = 'uCm3uZm1kGPlB7ATTlsMoA'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

mongoengine.connect(
    host='mongodb+srv://sergioRL:invierno%5F1@databases-k71qn.gcp.mongodb.net/test?retryWrites=true&w=majority'
)


redis = redis.StrictRedis(password='invierno')
mongoengine.connection.disconnect()
db = MongoEngine(app)
jwt = JWTManager(app)
CORS(app)

mongoengine.connection.disconnect()
from routes_endpoints import *

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
