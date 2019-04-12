from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
from flask import jsonify, request, make_response
from passlib.hash import pbkdf2_sha256 as sha256
from datetime import datetime as dt, timedelta as td
from reportlab.pdfgen import canvas
from models import Course, Teacher, LetterheadMetaData
from app import app
from marsh import *
from pdfs import *

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    try:
        teacher = Teacher.objects.get(rfc=data["rfc"])
        if sha256.verify(data["pin"], teacher["pin"]):
            jwtIdentity = teacher["rfc"]
            access_token = create_access_token(identity = jwtIdentity, expires_delta=td(hours=1))
            refresh_token = create_refresh_token(identity = jwtIdentity)
            return jsonify({"data": {
                'message': 'Logged in as {} {} {}'.format(teacher["name"], teacher["fstSurname"], teacher["sndSurname"]),
                'access_token': access_token,
                'refresh_token': refresh_token
            }})
        else:
            return jsonify({"message": "NIP incorrecto"})
    except Teacher.DoesNotExist:
        return jsonify({"message": "Docente no registrado"})

@app.route('/logout', methods=['GET'])
def logout_user():
    pass

@app.route('/courses', methods=['GET', 'POST'])
def courses():
    if (request.method == 'GET'):
        all_courses = Course.objects.all()
        data = courseSchemas.dump(all_courses)
        return jsonify(data)
    elif (request.method == 'POST'):
        data = request.get_json()
        Course(
            courseName = data["courseName"],
            teacherName = data["teacherName"],
            description = data["description"],
            dateStart = data["dateStart"],
            dateEnd = data["dateEnd"],
            totalHours = data["totalHours"],
            timetable = data["timetable"],
            place = data["place"],
            courseTo = data["courseTo"],
            modality = data["modality"],
            state = data["state"],
            serial = data["serial"]
        ).save()
        return jsonify({"message": "Curso guardado."})

@app.route('/course/<id>', methods=['GET', 'PUT', 'DELETE'])
def course(id):
    try:
        course = Course.objects.get(pk=id)
    except Course.DoesNotExist:
        return jsonify({"message": "Don't exists"})
    if (request.method == 'GET'):
        datos = courseSchema.dump(course)
        return jsonify(datos)
    elif (request.method == 'PUT'):
        attributes = ("name", "description", "dateStart", "dateEnd", "totalDays", "modality", "state", "serial")
        data = request.get_json()
        deserialized = courseSchema.load(data)
        for attribute in attributes:
            course[attribute] = deserialized[attribute]
        course.save()
        return jsonify(data)
    elif (request.method == 'DELETE'):
        deleted = course.name
        advice = "Curso " + str(deleted) + " eliminado"
        course.delete()
        return jsonify({"message":advice})

@app.route('/course/<course_id>/assistantList', methods=['GET'])
def assistantList_view(course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return jsonify({"message": "Curso inexistente"})
    all_teachers = Teacher.objects.all()
    teachers = []
    for teacher in all_teachers:
        teachers.append([
            teacher["name"] + ' ' + teacher["firstSurname"] + ' ' + teacher["secondSurname"],
            teacher["rfc"],
            teacher["studyType"]]
        )
    return assistantList(teachers, course)

@app.route('/teachers', methods=['GET', 'POST'])
def teachers():
    if (request.method == 'GET'):
        all_teachers = Teacher.objects.all()
        return jsonify(all_teachers)
    elif (request.method == 'POST'):
        data = request.get_json()
        Teacher(
            rfc = data["rfc"],
            name = data["name"],
            firstSurname = data["firstSurname"],
            secondSurname = data["secondSurname"],
            numberPhone = data["numberPhone"],
            email = data["email"],
            userType = data["userType"],
            departament = data["departament"],
            studyLevel = data["studyLevel"],
            speciality = data["speciality"],
            degree = data["degree"],
            pin = sha256.hash(data["pin"])
        ).save()
        return jsonify(data)

@app.route('/addInfo', methods=['GET', 'POST'])
def addinfoView():
    if(request.method == 'GET'):
        info = LetterheadMetaData.objects.all()
        return jsonify(info)
    elif(request.method == 'POST'):
        data = request.get_json()
        LetterheadMetaData(
            nameDocument = data['nameDocument'],
            typeDocument = data['typeDocument'],
            version = data['version'],
            emitDate = data['emitDate']
        ).save()
        return jsonify({"message": "tornado of souls"})

@app.route('/teacher/<id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def teacher(id):
    return jsonify({"message": "si pull"})

@app.route('/certificate_view/<id>', methods=['GET'])
def certificate_view(id):
    try:
        teacher = Teacher.objects.get(pk=id)
    except Teacher.DoesNotExist:
        return jsonify({"message": "Don't exists"})
    if (request.method == 'GET'):
        return certificate(teacher)



@app.route('/courses/coursesList', methods=['GET'])
def coursesList_view():
    all_courses = Course.objects.all()
    courses = []
    months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    for course in all_courses:
        courses.append([
            course["courseName"],
            course["description"],
            str(course["dateStart"].day)+"-"+str(course["dateEnd"].day)+" de "+months[course["dateStart"].month-1]+" del "+str(course["dateStart"].year),
            course["place"],
            str(course["totalHours"])+" hrs.",
            course["teacherName"],
            course["courseTo"]
        ])
    return coursesList(courses)

@app.errorhandler(404)
def page_not_found(error):
    error = {
        "errorType": "404",
        "message": "Pagina no encontrada"
    }
    return jsonify(error),404

# EXAMPLES
# """--------------  PyMongo  --------------"""
# @app.route('/courses', methods=['GET', 'POST'])
# def courses_view():
#     all_courses = mongo.db.course
#     courses = []
#     for c in all_courses.find():
#         data = json.loads(ju.dumps(c))
#         courses.append(data)
#     return jsonify(courses)

# @app.route('/course/<id>')
# def course_view(id):
#     course = mongo.db.course.find({"_id": ObjectId(id)})
#     data = json.loads(ju.dumps(course))
#     return jsonify(data)