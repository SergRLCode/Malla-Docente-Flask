from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_raw_jwt
from datetime import datetime as dt, timedelta as td
from passlib.hash import pbkdf2_sha256 as sha256
from models import Course, Teacher, BlacklistJWT
from flask import jsonify, request
from app import app, jwt

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):           # Verifica que el token no este en la blacklist
    jti = decrypted_token['jti']
    identity = decrypted_token['identity']
    _jwt = BlacklistJWT.objects.all()
    courses = Course.objects.all()
    for course in courses:
        hours = course['timetable'].split('-')
        if course['dateStart'].date() > dt.now().date():
            course['state'] = 'Por empezar'
        if course['dateStart'].date() <= dt.now().date():
            if dt.now().hour >= int(hours[0].replace(':00', "")):
                course['state'] = 'Cursando'
        if course['dateEnd'].date() <= dt.now().date():
            if course['dateEnd'].date() == dt.now().date():
                if dt.now().hour >= int(hours[1].replace(':00', "")):
                    course['state'] = 'Terminado'
            else:
                course['state'] = 'Terminado'
        course.save()
    for value in _jwt:
        if (jti==value['jwt']):
            return True             # Si regresa un booleano False, permite el accesso, si regresa True, marca que se revoco el JWT

@app.route('/login', methods=['POST'])
def login_user():                   # El tipico login de cada sistema
    data = request.get_json()
    try:
        teacher = Teacher.objects.get(rfc=data["rfc"])
        if sha256.verify(data["pin"], teacher["pin"]):
            numUser = 0 if teacher['userType']=='Administrador' else 1 if teacher['userType']=='Jefe de departamento' else 2 if teacher['userType']=='Comunicación' else 3
            jwtIdentity = [teacher["rfc"], numUser]
            try:
                previousTkn = BlacklistJWT.objects.filter(identity=jwtIdentity).values_list('identity')
                previousTkn.delete()
            except:
                pass
            access_token = create_access_token(identity = jwtIdentity, expires_delta=td(hours=24))
            refresh_token = create_refresh_token(identity = jwtIdentity)
            return (jsonify({"data": {
                'message': '{} {} {}'.format(teacher["name"], teacher["fstSurname"], teacher["sndSurname"]),
                'access_token': access_token
            }}), 200)
        else:
            return(jsonify({"data": {"message": "NIP incorrecto"}}), 401)
    except Teacher.DoesNotExist:
        return(jsonify({"data": {"message": "Docente no registrado"}}), 404)

@app.route('/logout', methods=['GET'])
@jwt_required
def logout_user():                  # Un logout que agrega el ID del JWT de acceso en una coleccion para evitar el uso de este JWT 
    _jwt = get_raw_jwt()['jti']
    _rfc = get_jwt_identity()[0]
    BlacklistJWT(
        jwt = _jwt,
        identity = _rfc
    ).save()
    return(jsonify({'message': 'Bye bye!'}), 200)
