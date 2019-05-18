from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
from pdfs import assistantList, coursesList, inscription, pollDocument
from models import Course, Teacher, LetterheadMetaData, Departament, BlacklistJWT, RequestCourse
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
def login_user():                   # El tipico login de cada sistema
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
            return (jsonify({"data": {
                'message': 'Logged in as {} {} {}'.format(teacher["name"], teacher["fstSurname"], teacher["sndSurname"]),
                'access_token': access_token,
                'refresh_token': refresh_token
            }}), 200)
        else:
            return(jsonify({"data": {"message": "NIP incorrecto"}}), 401)
    except Teacher.DoesNotExist:
        return(jsonify({"data": {"message": "Docente no registrado"}}), 404)

@app.route('/courses', methods=['GET', 'POST'])
@jwt_required
def courses():                      # Ruta para agregar un curso o consultar todos
    if (request.method == 'GET'):
        all_courses = Course.objects.filter(teacherRFC__ne=get_jwt_identity())
        data = courseSchemas.dump(all_courses)
        return(jsonify(data), 200)
    elif (request.method == 'POST'):
        data = request.get_json()
        all_rfc = Teacher.objects.all().values_list('rfc')
        if data['teacherRFC'] not in all_rfc:
            return(jsonify({"message": "Error, RFC no valido."}), 404)
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
            return(jsonify({"message": "Curso guardado."}), 200)

@app.route('/course/<name>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def course(name):                   # Ruta para consultar uno en especifico, editar info de un curso en especifico o borrar ese curso en especifico
    try:
        course = Course.objects.get(courseName=name)
    except Course.DoesNotExist:
        return(jsonify({"message": "Don't exists"}), 404)
    if (request.method == 'GET'):
        datos = courseSchema.dump(course)
        newDictToSend = datos[0]
        for key in ('teachersInCourse', 'id', 'serial'):
            del newDictToSend[key]
        teacherWillteach = Teacher.objects.filter(rfc=course['teacherRFC']).values_list("name", "fstSurname", "sndSurname")
        newDictToSend['teacherRFC'] = "{} {} {}".format(teacherWillteach[0][0], teacherWillteach[0][1], teacherWillteach[0][2])
        return(jsonify(newDictToSend), 200)
    elif (request.method == 'PUT'):
        attributes = ("courseName", "courseTo", "place", "description", "dateStart", "dateEnd", "modality", "state", "serial", "teacherRFC", "teachersInCourse", "timetable", "totalHours")
        data = request.get_json()
        for attribute in attributes:
            course[attribute] = data[attribute]
        course.save()
        return(jsonify({'message': 'Cambios guardados.'}), 200)
    elif (request.method == 'DELETE'):
        advice = "Curso {} eliminado".format(course.courseName)
        course.delete()
        return(jsonify({"message": advice}), 200)

@app.route('/teachers', methods=['GET', 'POST'])
def teachers():                     # Ruta para agregar un docente o consultar todos
    if (request.method == 'GET'):
        all_teachers = Teacher.objects.all()
        return(jsonify(all_teachers), 200)
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
        return(jsonify({'message': 'Docente agregado'}), 200)

@app.route('/teacher/<rfc>', methods=['GET', 'PUT', 'DELETE'])
def getTeacher(rfc):                # Ruta para consultar uno en especifico, editar info de un docente en especifico o borrar ese docente en especifico
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
        teacher['pin'] = sha256.hash(data["pin"])        
        teacher.save()
        return(jsonify({'message': 'Datos guardados.'}), 200)
    elif request.method == 'DELETE':
        advice = "{} eliminado".format(teacher.rfc)
        teacher.delete()
        return(jsonify({"message": advice}), 200)

@app.route('/courses/coursesList', methods=['GET'])
def coursesList_view():             # Ruta que regresa el documento PDF con lista de cursos disponibles 
    all_courses = Course.objects.all()
    if len(all_courses)!=0:
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
        return(coursesList(courses), 200)
    else:
        return(jsonify({'message': 'Sin cursos'}), 404)

@app.route('/course/<name>/assistantList', methods=['GET'])
def assistantList_view(name):       # Ruta que regresa el PDF con la lista de asistencia del curso seleccionado POR PARAMETRO EN RUTA
    try:
        course = Course.objects.get(courseName=name)
    except Course.DoesNotExist:
        return(jsonify({"message": "Curso inexistente"}), 404)
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
    return(assistantList(teachers, courseTeacherData, course), 200)

@app.route('/inscriptionDocument/<name>', methods=['GET'])
@jwt_required
def getInscriptionDocument(name):   # Ruta que regresa el PDF de la cedula de inscripcion del docente que solicita tomar un curso
    if(request.method == 'GET'):
        try:
            course = Course.objects.get(courseName=name)
        except Course.DoesNotExist:
            return(jsonify({"message": "Curso inexistente"}), 404)
        teacher = Teacher.objects.get(rfc=get_jwt_identity())
        departament = Departament.objects.get(name=teacher["departament"])
        if(teacher['rfc'] not in course['teachersInCourse']):
            teacherWillTeach = Teacher.objects.filter(rfc=course['teacherRFC']).values_list("name", "fstSurname", "sndSurname")
            return(inscription(teacher, departament, course, teacherWillTeach), 200)
        else:
            return(jsonify({"message":"Ya esta en el curso"}), 401)

@app.route('/course/<name>/poll', methods=['POST'])
@jwt_required
def poll_view(name):                # Ruta que regresa el PDF con la encuesta contestada por el docente
    if(request.method == 'POST'):
        courseData = Course.objects.filter(courseName=name).values_list('courseName', 'teacherRFC', 'place', 'dateStart', 'dateEnd', 'totalHours', 'timetable', 'teachersInCourse')
        if len(courseData)!=0:
            if get_jwt_identity() in courseData[0][7]:
                teacherThatTeach = Teacher.objects.filter(rfc=courseData[0][1]).values_list('name', 'fstSurname', 'sndSurname')
                departament = Teacher.objects.filter(rfc=get_jwt_identity()).values_list('departament')
                data = request.get_json()
                return(pollDocument(data, courseData, teacherThatTeach, departament[0]), 200)
            else:
                return(jsonify({'message': 'Curso no registrado.'}), 404)
        else:
            return(jsonify({'message': 'Curso inexistente.'}), 404)
        
@app.route('/refresh', methods=['GET'])
@jwt_refresh_token_required
def refresh_jwt():                  # Ruta que regresa otro JWT para el acceso 
    print(get_raw_jwt()['identity'])
    access_token = create_access_token(identity = get_jwt_identity(), expires_delta=td(hours=1))
    return(jsonify({'access_token': access_token}), 200)

@app.route('/logoutA', methods=['GET'])
@jwt_required
def logout_user():                  # Un logout que agrega el ID del JWT de acceso en una coleccion para evitar el uso de este JWT 
    _jwt = get_raw_jwt()['jti']
    _rfc = get_jwt_identity()
    BlacklistJWT(
        jwt = _jwt,
        identity = _rfc
    ).save()
    return(jsonify({'message': 'Bye bye!'}), 200)

@app.route('/logoutR', methods=['GET'])
@jwt_refresh_token_required
def logout_user2():                  # Un logout que agrega el ID del JWT de actualizacion en una coleccion para evitar el uso de este JWT
    _jwt = get_raw_jwt()['jti']
    _rfc = get_jwt_identity()
    BlacklistJWT(
        jwt = _jwt,
        identity = _rfc
    ).save()
    return(jsonify({'message': 'Bye bye!'}), 200)
            
#  ==> --> In Develop <-- <==

# Example of route with JWT 
@app.route('/pull')
@jwt_required
def teacher():
    return jsonify({"message": "Hello {}".format(get_jwt_identity())})

@app.route('/changePassword', methods=['POST'])
@jwt_required
def change_password():
    if(request.method=='POST'):
        data = request.get_json()
        teacher = Teacher.objects.get(rfc=get_jwt_identity())
        if(sha256.verify(data['pin'], teacher['pin'])):
            teacher['pin'] = sha256.hash(data['newPin'])
            teacher.save()
            return(jsonify({'message': 'Clave actualizada!'}), 200)
        else:
            return(jsonify({'message': 'Clave previa incorrecta'}), 401)

@app.route('/addTeacherinCourse/<course_name>', methods=['POST'])
def addTeacherinCourse_view(course_name):
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(courseName=course_name)   # Obtiene la informacion del curso seleccionado
        except Course.DoesNotExist:
            return(jsonify({"message": "Curso inexistente"}), 404)
        all_rfc = Teacher.objects.filter(rfc__ne=course['teacherRFC']).values_list('rfc')   # Obtiene todos los RFC de los docentes excepto el docente que imparte el curso
        courseWillTeach = Course.objects.filter(teacherRFC=data['rfc']).values_list('timetable', 'dateStart', 'dateEnd', 'courseName')
        restOfcourses = Course.objects.filter(courseName__ne=course_name).values_list('teachersInCourse', 'courseName') # Obtiene las listas de docentes de los demas cursos
        if(data['rfc'] not in all_rfc): # Verifica que exista el RFC                                   
            return(jsonify({'message': 'RFC invalido.'}), 401)
        else:   # En caso de que SI exista...
            if(data['rfc'] in course['teachersInCourse']):  # Verifica que el docente ya esta en la lista
                return(jsonify({"message": "Docente agregado previamente."}), 200)
            else:   # Si no...
                hoursCourseOne = course['timetable'].split('-')  # Una marihuanada
                if len(courseWillTeach)>0:
                    if(courseWillTeach[0][1] <= course['dateStart'] <= courseWillTeach[0][2] or courseWillTeach[0][1] <= course['dateEnd'] <= courseWillTeach[0][2]):
                        hoursCourseTwo = courseWillTeach[0][0].split('-')
                        if(hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1] or hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]):
                            return(jsonify({'message': 'Se empalma con la materia que imparte'}), 201)  
                # for rfcsCourse in restOfcourses: # Itera sobre el array que contiene los array de docentes de cada curso
                #     if data['rfc'] in rfcsCourse[0]:   # Si el docente ya esta en un curso...
                #         coursesData = Course.objects.filter(teachersInCourse=rfcsCourse[0], courseName=rfcsCourse[1]).values_list('timetable', 'dateStart', 'dateEnd', 'courseName') # Obtiene los datos del curso
                #         hoursCourseTwo = coursesData[0][0].split('-')   # Otra marihuanada
                #         if (coursesData[0][1] <= course['dateStart'] <= coursesData[0][2]) or (coursesData[0][1] <= course['dateEnd'] <= coursesData[0][2]): # Verifica que las fechas sean distintas, si no lo son...
                #             """La condicion de abajo verifica las marihuanadas que hice, o sea, que la hora de inicio y 
                #             finalizacion del curso, no este entre las horas de otro de inicio y finalizacion del curso"""
                #             if (hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1]) or (hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]): 
                #                 return jsonify({'message': 'Se empalma con otro curso a tomar'})
                if(course['teachersInCourse'] == ["No hay docentes registrados"]):
                    course['teachersInCourse'] = []
                course['teachersInCourse'].append(data['rfc'])
                course.save()
                return(jsonify({'message': 'Docente agregado con exito.'}), 200)

@app.route('/courseRequest/<name>', methods=['GET'])
@jwt_required
def course_request(name):
    course = Course.objects.filter(courseName=name).values_list('courseName')
    if len(course) == 0:
        return jsonify({'course': "Don't exists"})
    else:
        try:
            courseInRequest = RequestCourse.objects.get(course=course[0])
        except:
            RequestCourse(
                course = course[0],
                requests = get_jwt_identity()
            ).save()
            return jsonify({'message': 'Solicitud enviada!'})

@app.route('/removeTeacherinCourse/<name>', methods=['POST'])
def removeTeacherinCourse_view(name):
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(courseName=name)
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
        return jsonify({"message": "Added"})

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
        return jsonify({"message": "Added"})

@app.errorhandler(404)
def page_not_found(error):
    error = {
        "errorType": "404",
        "message": "Pagina no encontrada"
    }
    return(jsonify(error),404)
