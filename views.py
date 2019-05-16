from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
from pdfs import assistantList, coursesList, inscription, pollDocument
from models import Course, Teacher, LetterheadMetaData, Departament, BlacklistJWT
from datetime import datetime as dt, timedelta as td
from flask import jsonify, request, make_response
from passlib.hash import pbkdf2_sha256 as sha256
from reportlab.pdfgen import canvas
from app import app, jwt
from marsh import *

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    identity = decrypted_token['identity']
    _jwt = BlacklistJWT.objects.all()
    for value in _jwt:
        if (jti==value['jwt']):
            return True
    # Si regresa un booleano False, permite el accesso, si regresa True, marca que se revoco el JWT

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    try:
        teacher = Teacher.objects.get(rfc=data["rfc"])
        if sha256.verify(data["pin"], teacher["pin"]):
            jwtIdentity = teacher["rfc"]
            try:
                previousTkn = BlacklistJWT.objects.filter(identity=jwtIdentity).values_list('identity')
                previousTkn.delete()
            except:
                pass
            access_token = create_access_token(identity = jwtIdentity, expires_delta=td(hours=1))
            refresh_token = create_refresh_token(identity = jwtIdentity)
            return jsonify({"data": {
                'message': 'Logged in as {} {} {}'.format(teacher["name"], teacher["fstSurname"], teacher["sndSurname"]),
                'access_token': access_token,
                'refresh_token': refresh_token
            }})
        else:
            return jsonify({"data": {"message": "NIP incorrecto"}})
    except Teacher.DoesNotExist:
        return jsonify({"data": {"message": "Docente no registrado"}})

@app.route('/courses', methods=['GET', 'POST'])
@jwt_required
def courses():
    if (request.method == 'GET'):
        all_courses = Course.objects.filter(teacherRFC__ne=get_jwt_identity())
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
@app.route('/course/<name>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def course(name):
    try:
        course = Course.objects.get(courseName=name)
    except Course.DoesNotExist:
        return jsonify({"message": "Don't exists"})
    if (request.method == 'GET'):
        datos = courseSchema.dump(course)
        newDictToSend = datos[0]
        for key in ('teachersInCourse', 'id', 'serial'):
            del newDictToSend[key]
        teacherWillteach = Teacher.objects.filter(rfc=course['teacherRFC']).values_list("name", "fstSurname", "sndSurname")
        newDictToSend['teacherRFC'] = "{} {} {}".format(teacherWillteach[0][0], teacherWillteach[0][1], teacherWillteach[0][2])
        return jsonify(newDictToSend)
    elif (request.method == 'PUT'):
        attributes = ("courseName", "courseTo", "place", "description", "dateStart", "dateEnd", "modality", "state", "serial", "teacherRFC", "teachersInCourse", "timetable", "totalHours")
        data = request.get_json()
        for attribute in attributes:
            course[attribute] = data[attribute]
        course.save()
        return jsonify({'message': 'Cambios guardados.'})
    elif (request.method == 'DELETE'):
        advice = "Curso {} eliminado".format(course.courseName)
        course.delete()
        return jsonify({"message": advice})

@app.route('/course/<name>/assistantList', methods=['GET'])
def assistantList_view(name):
    try:
        course = Course.objects.get(courseName=name)
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
        return jsonify({'message': 'Docente agregado'})

@app.route('/teacher/<rfc>', methods=['GET', 'PUT', 'DELETE'])
def getTeacher(rfc):
    try:
        teacher = Teacher.objects.get(rfc=rfc)
    except Teacher.DoesNotExist:
        return jsonify({'message': 'Docente no registrado'})
    if request.method == 'GET':
        data = teacherSchema.dump(teacher)
        dictReturn = data[0]
        for value in ('id', 'pin'):
            del dictReturn[value]
        return jsonify(dictReturn)
    elif request.method == 'PUT':
        attributes = ('rfc', 'name', 'fstSurname', 'sndSurname', 'numberPhone', 'email', 'studyLevel', 'degree', 'speciality', 'departament', 'schedule', 'position', 'userType')
        data = request.get_json()
        for value in attributes:
            teacher[value] = data[value]
        teacher['pin'] = sha256.hash(data["pin"])        
        teacher.save()
        return jsonify({'message': 'Datos guardados.'})
    elif request.method == 'DELETE':
        advice = "{} eliminado".format(teacher.rfc)
        teacher.delete()
        return jsonify({"message": advice})

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
            course["dateStart"],
            course["dateEnd"],
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
@app.route('/inscriptionDocument/<name>', methods=['POST'])
def getInscriptionDocument(name):
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(courseName=name)
        except Course.DoesNotExist:
            return jsonify({"message": "Curso inexistente"})
        teacher = Teacher.objects.get(rfc=data['rfc'])
        departament = Departament.objects.get(name=teacher["departament"])
        if(teacher['rfc'] in course['teachersInCourse']):
            teacherWillTeach = Teacher.objects.filter(rfc=course['teacherRFC']).values_list("name", "fstSurname", "sndSurname")
            return inscription(teacher, departament, course, teacherWillTeach)
        else:
            return jsonify({"message":"error"})
            
#  ==> --> In Develop <-- <==
@app.route('/course/<name>/poll', methods=['POST'])
@jwt_required
def poll_view(name):
    courseData = Course.objects.filter(courseName=name).values_list('courseName', 'teacherRFC', 'place', 'dateStart', 'dateEnd', 'totalHours', 'timetable', 'teachersInCourse')
    if len(courseData)!=0:
        if get_jwt_identity() in courseData[0][7]:
            teacherThatTeach = Teacher.objects.filter(rfc=courseData[0][1]).values_list('name', 'fstSurname', 'sndSurname')
            departament = Teacher.objects.filter(rfc=get_jwt_identity()).values_list('departament')
            if(request.method == 'POST'):
                data = request.get_json()
                return pollDocument(data, courseData, teacherThatTeach, departament[0])
        else:
            return jsonify({'message': 'Curso no registrado.'})
    else:
        return jsonify({'message': 'Curso inexistente.'})
        
@app.route('/refresh', methods=['GET'])
@jwt_refresh_token_required
def refresh_jwt():
    print(get_raw_jwt()['identity'])
    access_token = create_access_token(identity = get_jwt_identity(), expires_delta=td(hours=1))
    return jsonify({'access_token': access_token})

# Example of route with JWT 
@app.route('/pull')
@jwt_required
def teacher():
    return jsonify({"message": "Hello {}".format(get_jwt_identity())})

@app.route('/logoutA', methods=['GET'])
@jwt_required
def logout_user():
    _jwt = get_raw_jwt()['jti']
    _rfc = get_jwt_identity()
    BlacklistJWT(
        jwt = _jwt,
        identity = _rfc
    ).save()
    return jsonify({'message': 'Bye bye!'})

@app.route('/logoutR', methods=['GET'])
@jwt_refresh_token_required
def logout_user2():
    _jwt = get_raw_jwt()['jti']
    _rfc = get_jwt_identity()
    BlacklistJWT(
        jwt = _jwt,
        identity = _rfc
    ).save()
    return jsonify({'message': 'Bye bye!'})

@app.route('/addTeacherinCourse/<course_id>', methods=['POST'])
def addTeacherinCourse_view(course_id):
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(pk=course_id)   # Obtiene la informacion del curso seleccionado
        except Course.DoesNotExist:
            return jsonify({"message": "Curso inexistente"})
        all_rfc = Teacher.objects.filter(rfc__ne=course['teacherRFC']).values_list('rfc')   # Obtiene todos los RFC de los docentes excepto el docente que imparte el curso
        courseWillTeach = Course.objects.filter(teacherRFC=data['rfc']).values_list('timetable', 'dateStart', 'dateEnd', 'courseName')
        restOfcourses = Course.objects.filter(pk__ne=course_id).values_list('teachersInCourse', 'courseName') # Obtiene las listas de docentes de los demas cursos
        if(data['rfc'] not in all_rfc): # Verifica que exista el RFC                                   
            return jsonify({'message': 'RFC invalido.'})
        else:   # En caso de que SI exista...
            if(data['rfc'] in course['teachersInCourse']):  # Verifica que el docente ya esta en la lista
                return jsonify({"message": "Docente agregado previamente."})
            else:   # Si no...
                hoursCourseOne = course['timetable'].split('-')  # Una marihuanada
                if len(courseWillTeach)>0:
                    if(courseWillTeach[0][1] <= course['dateStart'] <= courseWillTeach[0][2] or courseWillTeach[0][1] <= course['dateEnd'] <= courseWillTeach[0][2]):
                        hoursCourseTwo = courseWillTeach[0][0].split('-')
                        if(hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1] or hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]):
                            return jsonify({'message': 'Se empalma con la materia que imparte'})     
                for rfcsCourse in restOfcourses: # Itera sobre el array que contiene los array de docentes de cada curso
                    if data['rfc'] in rfcsCourse[0]:   # Si el docente ya esta en un curso...
                        coursesData = Course.objects.filter(teachersInCourse=rfcsCourse[0], courseName=rfcsCourse[1]).values_list('timetable', 'dateStart', 'dateEnd', 'courseName') # Obtiene los datos del curso
                        hoursCourseTwo = coursesData[0][0].split('-')   # Otra marihuanada
                        if (coursesData[0][1] <= course['dateStart'] <= coursesData[0][2]) or (coursesData[0][1] <= course['dateEnd'] <= coursesData[0][2]): # Verifica que las fechas sean distintas, si no lo son...
                            """La condicion de abajo verifica las marihuanadas que hice, o sea, que la hora de inicio y 
                            finalizacion del curso, no este entre las horas de otro de inicio y finalizacion del curso"""
                            if (hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1]) or (hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]): 
                                return jsonify({'message': 'Se empalma con otro curso a tomar'})
                if(course['teachersInCourse'] == ["No hay docentes registrados"]):
                    course['teachersInCourse'] = []
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
            if not course['teachersInCourse']:
                course['teachersInCourse'] = ['No hay docentes registrados'] # La lista no debe estar vacia, porque lo toma como nulo y se borra el atributo del documento
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
