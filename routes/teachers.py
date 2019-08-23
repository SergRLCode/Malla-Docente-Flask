from flask_jwt_extended import jwt_required, get_jwt_identity, get_raw_jwt
from models import Course, Teacher, LetterheadMetaData, Qualified, BlacklistJWT, RequestCourse, BlacklistRequest
from datetime import datetime as dt, timedelta as td
from passlib.hash import pbkdf2_sha256 as sha256
from auth import requires_access_level
from mongoengine import errors as e
from flask import jsonify, request
from app import app
from marsh import *

@app.route('/teachers', methods=['GET', 'POST'])
@jwt_required
def teachers():                     # Ruta para agregar un docente o consultar todos
    if (request.method == 'GET'):
        teachers = Teacher.objects.all()
        all_teachers = teacherSchemas.dump(teachers)
        for teacher in all_teachers[0]:
            teacher['name'] = "{} {} {}".format(teacher['name'], teacher['fstSurname'], teacher['sndSurname'])
            if teacher['internal'] == False:
                teacher['departament'] = "Externo"
            if teacher['userType'] == "Comunicación":
                teacher['departament'] = "Comunicación"
            del teacher['fstSurname']
            del teacher['sndSurname']
        return(jsonify(all_teachers[0]), 200)
    elif (request.method == 'POST'):
        data = request.get_json()
        if data['studyLevel'] == "Otro":
            data['studyLevel'] = data['otherStudyLevel']
        if data['internal'] != False:
            try:
                Teacher(
                    rfc = data["rfc"],
                    name = data["name"],
                    fstSurname = data["fstSurname"],
                    sndSurname = data["sndSurname"],
                    numberPhone = data["numberPhone"],
                    email = data["email"],
                    internal = data["internal"],
                    studyLevel = data["studyLevel"],
                    degree = data["degree"],
                    speciality = data["speciality"],
                    departament = data["departament"],
                    schedule = data["schedule"],
                    position = data["position"],
                    userType = data["userType"],
                    pin = sha256.hash(data["pin"])
                ).save()
            except:
                return(jsonify({'message': 'Error, verifique bien la informacion'}), 401)
            return(jsonify({'message': 'Docente agregado'}), 200)
        else:
            try:
                Teacher(
                    rfc = data["rfc"],
                    name = data["name"],
                    fstSurname = data["fstSurname"],
                    sndSurname = data["sndSurname"],
                    numberPhone = data["numberPhone"],
                    email = data["email"],
                    internal = data["internal"],
                    studyLevel = data["studyLevel"],
                    degree = data["degree"],
                    speciality = data["speciality"],
                    departament = "",
                    schedule = "",
                    position = "",
                    userType = data["userType"],
                    pin = sha256.hash(data["pin"])
                ).save()
                return(jsonify({'message': 'Docente externo registrado'}), 200)
            except:
                return(jsonify({'message': 'Docente previamente registrado'}), 401)

@app.route('/teacher/<rfc>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def teacher(rfc):                # Ruta para consultar uno en especifico, editar info de un docente en especifico o borrar ese docente en especifico
    try:
        teacher = Teacher.objects.get(rfc=rfc)
    except Teacher.DoesNotExist:
        return(jsonify({'message': 'Docente no registrado'}), 404)
    if request.method == 'GET':
        data = teacherSchema.dump(teacher)
        dictReturn = data[0]
        for value in ('id', 'pin'):
            del dictReturn[value]
        return(jsonify(dictReturn), 200)
    elif request.method == 'PUT':
        attributes = ('rfc', 'name', 'fstSurname', 'sndSurname', 'numberPhone', 'email', 'studyLevel', 'degree', 'speciality', 'departament', 'schedule', 'position', 'userType')
        data = request.get_json()
        for value in attributes:
            teacher[value] = data[value]    
        prevTeacher = Teacher.objects.get(position='Jefe de departamento', departament=data['departament'])
        if(data['position']=='Jefe de departamento' and data['rfc']!=prevTeacher['rfc']):       # En caso que haya cambio de jefe, se cambia automaticamente al anterior
            prevTeacher['userType'] = 'Docente'
            prevTeacher['position'] = 'Docente chido'
            prevTeacher.save()      
        try:
            teacher.save()
        except e.NotUniqueError:
            return jsonify({'message': 'RFC duplicado'}), 403
        else:
            return(jsonify({'message': 'Datos guardados.'}), 200)
    elif request.method == 'DELETE':
        courses = Course.objects.filter(teachersInCourse__contains=teacher.rfc)
        requests = RequestCourse.objects.filter(requests__contains=teacher.rfc)
        blacklist = BlacklistRequest.objects.filter(requests__contains=teacher.rfc)
        for course in courses:
            course['teachersInCourse'].remove(rfc)
            if not course['teachersInCourse']:
                course['teachersInCourse'] = ['No hay docentes registrados'] # La lista no debe estar vacia, porque lo toma como nulo y se borra el atributo del documento
            course.save()
        for reqst in requests:
            reqst['requests'].remove(rfc)
            reqst.save()
            if(len(reqst['requests'])==0):
                reqst.delete()
        for reqst in blacklist:
            reqst['requests'].remove(rfc)
            reqst.save()
            if(len(reqst['requests'])==0):
                reqst.delete()
        advice = "{} eliminado".format(teacher.rfc)
        teacher.delete()
        return(jsonify({"message": advice}), 200)

@app.route('/teachersByDep/<course>', methods=['GET'])
@jwt_required
def teachersByDep(course):       # Ruta que visualiza los docentes por departamento que no sean jefes de departamento para sugerir docentes
    if request.method == 'GET':    
        teacherList = []
        department = Teacher.objects.filter(rfc=get_jwt_identity()[0]).values_list('departament')
        teachersData = Teacher.objects.filter(departament=department[0]).values_list('rfc', 'name', 'fstSurname', 'sndSurname', 'userType')
        _course = Course.objects.filter(courseName=course).values_list('teacherRFC','teachersInCourse')
        try:
            _requestCourse = RequestCourse.objects.get(course=course)
            _blacklistRequest = BlacklistRequest.objects.get(course=course)
        except RequestCourse.DoesNotExist:
            try:
                _blacklistRequest = BlacklistRequest.objects.get(course=course)
            except BlacklistRequest.DoesNotExist:
                for val in teachersData:
                    if val[4] != 'Jefe de departamento' and val[0] != _course[0][0] and val[0] not in _course[0][1]:
                        print(val)        
                        teacherList.append({
                            'rfc': val[0],
                            'name': "{} {} {}".format(val[1], val[2], val[3])
                        })
            else:
                for val in teachersData:
                    if val[4] != 'Jefe de departamento' and val[0] != _course[0][0] and val[0] not in _course[0][1] and val[0] not in _blacklistRequest['requests']:
                        teacherList.append({
                            'rfc': val[0],
                            'name': "{} {} {}".format(val[1], val[2], val[3])
                        })
        except BlacklistRequest.DoesNotExist:
            for val in teachersData:
                if val[4] != 'Jefe de departamento' and val[0] != _course[0][0] and val[0] not in _course[0][1] and val[0] not in _requestCourse['requests']:
                    teacherList.append({
                        'rfc': val[0],
                        'name': "{} {} {}".format(val[1], val[2], val[3])
                    })
        else:
            for val in teachersData:
                if val[4] != 'Jefe de departamento' and val[0] != _course[0][0] and val[0] not in _course[0][1] and val[0] not in _requestCourse['requests'] and val[0] not in _blacklistRequest['requests']:
                    teacherList.append({
                        'rfc': val[0],
                        'name': "{} {} {}".format(val[1], val[2], val[3])
                    })
        finally:
            return jsonify({'teachers': teacherList}), 200

@app.route('/getTeachersByDep', methods=['GET'])
@jwt_required
@requires_access_level([1])
def _getTeachersByDep():
    if request.method == 'GET':
        teachers = list()
        _departament = Teacher.objects.filter(rfc=get_jwt_identity()[0], userType='Jefe de departamento').values_list('departament')
        teachersOf = Teacher.objects.filter(departament=_departament[0])
        for val in teachersOf:
            if val['rfc'] != get_jwt_identity()[0]:
                teachers.append({
                    'name': '%s %s %s'%(val['name'], val['fstSurname'], val['sndSurname']),
                    'rfc': val['rfc'],
                    'studyLevel': val['studyLevel'],
                    'degree': val['degree']
                })

        return jsonify({'teachers': teachers})

@app.route('/changePassword', methods=['POST'])
@jwt_required
def change_password():          # No es necesario mencionar para que es, con el puro nombre de la funcion se ve
    if(request.method=='POST'):
        data = request.get_json()
        teacher = Teacher.objects.get(rfc=get_jwt_identity()[0])
        if(sha256.verify(data['pin'], teacher['pin'])):
            teacher['pin'] = sha256.hash(data['newPin'])
            teacher.save()
            return(jsonify({'message': 'Clave actualizada!'}), 200)
        else:
            return(jsonify({'message': 'Clave previa incorrecta'}), 401)
