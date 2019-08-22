from flask_jwt_extended import jwt_required
from models import LetterheadMetaData
from flask import jsonify, request
from app import app
from marsh import *

@app.route('/metadata', methods=['GET', 'POST'])
@jwt_required
def metadata_route():                      # Only works to add meta data for each letterhead, next change will update meta data
    if(request.method == 'GET'):
        info = LetterheadMetaData.objects.all()
        data = letterheadSchemas.dump(info)
        return jsonify(data[0])
    elif(request.method == 'POST'):
        data = request.get_json()
        LetterheadMetaData(
            nameDocument = data['nameDocument'],
            shortName = data['shortName'],
            typeDocument = data['typeDocument'],
            version = data['version'],
            emitDate = data['emitDate']
        ).save()
        return(jsonify({"message": "Added"}), 200)

@app.route('/metadata/<doc>', methods=['GET','PUT'])
@jwt_required
def metadata_u(doc):
    info = LetterheadMetaData.objects.get(shortName=doc)
    if(request.method=='GET'):
        data = letterheadSchema.dump(info)
        return jsonify(data[0])
    if request.method=='PUT':
        attributes = ('shortName', 'nameDocument', 'typeDocument', 'version', 'emitDate')
        data = request.get_json()
        for val in attributes:
            info[val] = data[val]
        info.save()
        return jsonify({'message': 'Datos guardados!.'})
