# -*- coding: utf-8 -*-

from views import *
from flask_jwt_extended import JWTManager
from flask_mongoengine import MongoEngine
from flask import Flask

app = Flask(__name__)
app.config['MONGODB_DB'] = 'Capacitacion'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'

jwt = JWTManager(app)

# database_name_auth = 'Teacher'

db = MongoEngine(app)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

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
