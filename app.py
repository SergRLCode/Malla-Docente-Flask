# -*- coding: utf-8 -*-

from flask_jwt_extended import JWTManager
from flask_mongoengine import MongoEngine
from flask_cors import CORS
from flask import Flask

app = Flask(__name__)
app.config['MONGODB_DB'] = 'Capacitacion'
app.config['JWT_SECRET_KEY'] = 'uCm3uZm1kGPlB7ATTlsMoA'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

db = MongoEngine(app)
jwt = JWTManager(app)
CORS(app)

from views import *

if __name__ == '__main__':
   app.run(debug=True, port=5001, host='192.168.1.77')

# First upload
# git init 
# git add . or folder
# git commit -m "Mi comentario"
# git set-url remote origin git@github.com:My_User/Repository.git
# git pull --rebase origin master
# git push origin master
# Nota: origin es la carpeta de origen, o sea en donde esta el proyecto xd

# Upload proyect Github
# git init 
# git add . or folder
# git commit -m "Mi comentario"
# git push origin master