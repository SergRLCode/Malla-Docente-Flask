from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
from pdfs import assistantList, coursesList, inscription, pollDocument
from models import Course, Teacher, LetterheadMetaData, Departament
from datetime import datetime as dt, timedelta as td
from flask import jsonify, request, make_response
from passlib.hash import pbkdf2_sha256 as sha256
from reportlab.pdfgen import canvas
from app import app
from marsh import *

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

@app.route('/courses', methods=['GET', 'POST'])
def courses():
    if (request.method == 'GET'):
        all_courses = Course.objects.all()
        data = courseSchemas.dump(all_courses)
        return jsonify(data)
    elif (request.method == 'POST'):
        data = request.get_json()
        all_rfc = Teacher.objects.all().values_list('rfc')
        if data['teacherRFC'] not in all_rfc:
            return jsonify({"message": "Error, RFC no valido."})
        else:
            Course(
                courseName = data["courseName"],
                teacherRFC = data["teacherRFC"],
                modality = data["modality"],
                dateStart = data["dateStart"],
                dateEnd = data["dateEnd"],
                timetable = data["timetable"],
                place = data["place"],
                teachersInCourse = data["teachersInCourse"],
                description = data["description"],
                totalHours = data["totalHours"],
                courseTo = data["courseTo"],
                serial = data["serial"],
                state = data["state"]
            ).save()         
            return jsonify({"message": "Curso guardado."})
# Seguir modificando Modelo
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
        attributes = ("courseName", "courseTo", "place", "description", "dateStart", "dateEnd", "modality", "state", "serial", "teacherRFC", "teachersInCourse", "timetable", "totalHours")
        data = request.get_json()
        for attribute in attributes:
            course[attribute] = data[attribute]
        course.save()
        return jsonify(data)
    elif (request.method == 'DELETE'):
        deleted = course.name
        advice = "Curso {} eliminado".format(deleted)
        course.delete()
        return jsonify({"message":advice})

@app.route('/course/<course_id>/assistantList', methods=['GET'])
def assistantList_view(course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return jsonify({"message": "Curso inexistente"})
    courseTeacher = Teacher.objects.get(rfc=course['teacherRFC'])
    courseTeacherData = [
        "{} {} {}".format(courseTeacher["name"], courseTeacher["fstSurname"], courseTeacher["sndSurname"]),
        courseTeacher["rfc"]
    ]
    teachersinCourse = Teacher.objects.filter(rfc__ne=course['teacherRFC'])
    teachers = []
    for teacher in teachersinCourse:
        if(teacher["rfc"] in course['teachersInCourse']):
            teachers.append([
                "{} {} {}".format(teacher["name"], teacher["fstSurname"], teacher["sndSurname"]),
                teacher["rfc"],
                teacher["departament"]]
        )
    return assistantList(teachers, courseTeacherData, course)

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
            fstSurname = data["fstSurname"],
            sndSurname = data["sndSurname"],
            numberPhone = data["numberPhone"],
            email = data["email"],
            studyLevel = data["studyLevel"],
            degree = data["degree"],
            speciality = data["speciality"],
            departament = data["departament"],
            schedule = data["schedule"],
            position = data["position"],
            userType = data["userType"],
            pin = sha256.hash(data["pin"])
        ).save()
        return jsonify(data)

@app.route('/courses/coursesList', methods=['GET'])
def coursesList_view():
    all_courses = Course.objects.all()
    courses = []
    months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    for course in all_courses:
        teacherName = Teacher.objects.filter(rfc=course["teacherRFC"]).values_list("name", "fstSurname", "sndSurname")
        courses.append([
            course["courseName"],
            course["description"],
            "{}-{} de {} del {}".format(course["dateStart"].day, course["dateEnd"].day, months[course["dateStart"].month-1], course["dateStart"].year),
            course["place"],
            "{} hrs.".format(course["totalHours"]),
            "{} {} {}".format(teacherName[0][0], teacherName[0][1], teacherName[0][2]),
            course["courseTo"]
        ])
    return coursesList(courses)
# --> Lee esto: Lo estoy haciendo incorrectamente pero solo para prueba, porque el usuario no enviara su RFC, sino que por medio del JSON Web Token, se obtendra el RFC para obtener el documento <--
# --> Lee esto: Lo estoy haciendo incorrectamente pero solo para prueba, porque el usuario no enviara su RFC, sino que por medio del JSON Web Token, se obtendra el RFC para obtener el documento <--
# --> Lee esto: Lo estoy haciendo incorrectamente pero solo para prueba, porque el usuario no enviara su RFC, sino que por medio del JSON Web Token, se obtendra el RFC para obtener el documento <--
# --> Lee esto: Lo estoy haciendo incorrectamente pero solo para prueba, porque el usuario no enviara su RFC, sino que por medio del JSON Web Token, se obtendra el RFC para obtener el documento <--
# --> Lee esto: Lo estoy haciendo incorrectamente pero solo para prueba, porque el usuario no enviara su RFC, sino que por medio del JSON Web Token, se obtendra el RFC para obtener el documento <--
# --> Lee esto: Lo estoy haciendo incorrectamente pero solo para prueba, porque el usuario no enviara su RFC, sino que por medio del JSON Web Token, se obtendra el RFC para obtener el documento <--
@app.route('/inscriptionDocument/<course_id>', methods=['POST'])
def getInscriptionDocument(course_id):
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return jsonify({"message": "Curso inexistente"})
        teacher = Teacher.objects.get(rfc=data['rfc'])
        departament = Departament.objects.get(name=teacher["departament"])
        if(teacher['rfc'] in course['teachersInCourse']):
            teacherWillTeach = Teacher.objects.filter(rfc=course['teacherRFC']).values_list("name", "fstSurname", "sndSurname")
            return inscription(teacher, departament, course, teacherWillTeach)
        else:
            return jsonify({"message":"error"})
            
@app.route('/poll', methods=['GET'])
def poll_view():
    if(request.method == 'GET'):
        # data = request.get_json()
        data = {	
            "one": 5,
	        "two": 5,
	        "three": 5,
	        "four": 5, 
	        "five": 4,
	        "six": 5,
	        "seven": 5,
	        "eight": 5,
	        "nine": 5,
	        "ten": 5,
	        "eleven": 4,
	        "twelve": 4,
	        "thirteen": 4,
	        "fourteen": "No",
	        "explication": "porque nel prro",
	        "commentaries": "pos estuvo chido el curso la neta que si"
        }
        return pollDocument(data)

#  ==> --> In Develop <-- <==

@app.route('/logout', methods=['GET'])
def logout_user():
    pass

@app.route('/addTeacherinCourse/<course_id>', methods=['POST'])
def addTeacherinCourse_view(course_id):
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return jsonify({"message": "Curso inexistente"})
        restOfcourses = Course.objects.filter(pk__ne=course_id).values_list('teachersInCourse')
        all_rfc = Teacher.objects.filter(rfc__ne=course['teacherRFC']).values_list('rfc')
        if(data['rfc'] not in all_rfc):
            return jsonify({'message': 'RFC invalido.'})
        else:
            if(data['rfc'] in course['teachersInCourse']):
                return jsonify({"message": "Docente agregado previamente."})
            else:
                for rfcsCourse in restOfcourses:
                    if data['rfc'] in rfcsCourse:
                        timetable = Course.objects.filter(teachersInCourse=rfcsCourse).values_list('timetable', 'dateStart', 'dateEnd')
                        courseOne = timetable[0][0].split('-')
                        courseTwo = course['timetable'].split('-')
                        if courseTwo[0] >= courseOne[0] <= courseTwo[1] or courseTwo[0] >= courseOne[1] <= courseTwo[1]:
                            return jsonify({'message': 'Se empalma'})
                        return jsonify({'message': 'Ya esta en uno'})
                course['teachersInCourse'].append(data['rfc'])
                course.save()
                return jsonify({'message': 'Docente agregado con exito.'})

@app.route('/removeTeacherinCourse/<course_id>', methods=['POST'])
def removeTeacherinCourse_view(course_id):
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return jsonify({"message": "Curso inexistente"})
        if(data['rfc'] in course['teachersInCourse']):
            course['teachersInCourse'].remove(data['rfc'])
            course.save()
            return jsonify({"message": "Docente dado de baja exitosamente"})
        else:
            return jsonify({"message": "No existe en la lista"})

# Only works to add meta data for each letterhead, next change will update meta data
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

# Only works to add departament info for each letterhead, next change will update departament info
@app.route('/addDepartament', methods=['GET', 'POST'])
def adddepaView():
    if(request.method == 'GET'):
        info = Departament.objects.all()
        return jsonify(info)
    elif(request.method == 'POST'):
        data = request.get_json()
        Departament(
            name = data["name"],
            boss = data["boss"]
        ).save()
        return jsonify({"message": "san sebastian"})

# Example of route with JWT 
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
        return "hola"

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