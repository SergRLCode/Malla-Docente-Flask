from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
from pdfs import assistantList, coursesList, inscription, pollDocument, concentrated
from models import Course, Teacher, LetterheadMetaData, Departament, BlacklistJWT, RequestCourse, BlacklistRequest
from datetime import datetime as dt, timedelta as td
from flask import jsonify, request, make_response
from passlib.hash import pbkdf2_sha256 as sha256
from reportlab.pdfgen import canvas
from app import app, jwt
from marsh import *

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):           # Verifica que el token no este en la blacklist
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
            numUser = 0 if teacher['userType']=='Administrador' else 1 if teacher['userType']=='Jefe de departamento' else 2 if teacher['userType']=='Comunicación' else 3
            return (jsonify({"data": {
                'message': 'Logged in as {} {} {}'.format(teacher["name"], teacher["fstSurname"], teacher["sndSurname"]),
                'type': numUser,
                'access_token': access_token,
                'refresh_token': refresh_token
            }}), 200)
        else:
            return(jsonify({"data": {"message": "NIP incorrecto"}}), 401)
    except Teacher.DoesNotExist:
        return(jsonify({"data": {"message": "Docente no registrado"}}), 404)
        
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

@app.route('/courses', methods=['GET', 'POST'])
# @jwt_required
def courses():                      # Ruta para agregar un curso o consultar todos
    if (request.method == 'GET'):
        all_courses = Course.objects.filter()
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
                description = data["description"],
                totalHours = data["totalHours"],
                courseTo = data["courseTo"],
                teachersInCourse = data['teachersInCourse'],
                typeCourse = data["typeCourse"],
                serial = data["serial"]
            ).save()
            return(jsonify({"message": "Curso guardado."}), 200)

@app.route('/availableCourses', methods=['GET'])
@jwt_required
def available_courses():            # Ruta que retorna una lista con los cursos disponibles, siendo el dia de inicio mayor a la fecha del servidor
    if(request.method=='GET'):
        availableCourses = Course.objects.filter(dateStart__gte=dt.now().date()).values_list('courseName', 'teacherRFC')
        arrayToSend = []
        for vals in availableCourses:
            teacherName = Teacher.objects.filter(rfc=vals[1]).values_list('name', 'fstSurname', 'sndSurname')
            completeName = "{} {} {}".format(teacherName[0][0], teacherName[0][1], teacherName[0][2])
            arrayToSend.append({'courseName': vals[0], 'teacherName': completeName})
        return(jsonify({'message': arrayToSend}), 200)

@app.route('/course/<name>', methods=['GET', 'PUT', 'DELETE'])
# @jwt_required
def course(name):                   # Ruta para consultar uno en especifico, editar info de un curso en especifico o borrar ese curso en especifico
    try:
        course = Course.objects.get(courseName=name)
    except Course.DoesNotExist:
        return(jsonify({"message": "Don't exists"}), 404)
    if (request.method == 'GET'):################################################### Ya no moverle
        datos = courseSchema.dump(course)
        newDictToSend = datos[0]
        print(newDictToSend)
        for key in ('teachersInCourse', 'id', 'serial'):
            del newDictToSend[key]
        teacherWillteach = Teacher.objects.filter(rfc=course['teacherRFC']).values_list("name", "fstSurname", "sndSurname")
        newDictToSend['teacherRFC'] = "{} {} {}".format(teacherWillteach[0][0], teacherWillteach[0][1], teacherWillteach[0][2])
        return(jsonify(newDictToSend), 200)
    elif (request.method == 'PUT'):################################################# Ya no moverle
        data = request.get_json()
        attributes = ("courseName", "courseTo", "place", "description", "dateStart", "dateEnd", "modality", "state", "timetable", "totalHours", "typeCourse")
        all_rfc = Teacher.objects.all().values_list('rfc')        
        for attribute in attributes:
            course[attribute] = data[attribute]
        if data['teacherRFC'] in all_rfc:
            course['teacherRFC'] = data['teacherRFC']
        else:
            return(jsonify({'message': 'RFC invalido'}), 404)
        course.save()
        return(jsonify({'message': 'Cambios guardados.'}), 200)
    elif (request.method == 'DELETE'):############################################### Ya no moverle
        advice = "Curso {} eliminado".format(course.courseName)
        course.delete()
        return(jsonify({"message": advice}), 200)

@app.route('/courseRequest/<name>', methods=['GET'])
@jwt_required
def course_request(name):           # Ruta en la cual el docente agrega su RFC para peticion de tomar un curso
    course = Course.objects.filter(courseName=name).values_list('timetable', 'dateStart', 'dateEnd', 'courseName', 'teacherRFC')
    courseWillTeach = Course.objects.filter(teacherRFC=get_jwt_identity()).values_list('timetable', 'dateStart', 'dateEnd', 'courseName', 'teacherRFC')
    requestedAlready = Course.objects.filter(courseName=name, teachersInCourse__contains=get_jwt_identity())
    blacklisted = BlacklistRequest.objects.filter(course=name)
    if(len(blacklisted)>0):                                                       # checa que no este en la blacklist
        return(jsonify({'message': 'Ya no puede solicitar el curso'}), 401)
    if(len(requestedAlready)>0):                                                    # checar que ya esta en el curso
        return(jsonify({'message': 'Ya estas dentro del curso'}), 401)
    if len(course) == 0:                                                        # checa si existe el curso
        return(jsonify({'message': "Curso inexistente"}), 401)
    else:                                                                       # NOTA: preguntar hasta cuando se puede solicitar un curso
        if(course[0][4]==get_jwt_identity()):
            return(jsonify({'message': 'Usted imparte el curso'}), 401)    
        else:
            try:
                courseInRequest = RequestCourse.objects.get(course=course[0][3])
                if get_jwt_identity() not in courseInRequest['requests']:
                    if len(courseWillTeach)>0:
                        if(courseWillTeach[0][1] <= course[0][1] <= courseWillTeach[0][2] or courseWillTeach[0][1] <= course[0][2] <= courseWillTeach[0][2]):
                            hoursCourseOne = course[0][0].split('-')  # Una marihuanada
                            hoursCourseTwo = courseWillTeach[0][0].split('-')
                            if(hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1] or hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]):
                                return(jsonify({'message': 'Se empalma con la materia que imparte'}), 401)  
                    courseInRequest["requests"].append(get_jwt_identity())
                    courseInRequest.save()
                    return(jsonify({'message': 'Solicitud enviada!'}), 200)
                else:
                    return(jsonify({'message': 'Ya ha solicitado el curso.'}), 401)
            except:
                if len(courseWillTeach)>0:
                    if(courseWillTeach[0][1] <= course[0][1] <= courseWillTeach[0][2] or courseWillTeach[0][1] <= course[0][2] <= courseWillTeach[0][2]):
                        hoursCourseOne = course[0][0].split('-')  # Una marihuanada
                        hoursCourseTwo = courseWillTeach[0][0].split('-')
                        if(hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1] or hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]):
                            return(jsonify({'message': 'Se empalma con la materia que imparte'}), 401)  
                RequestCourse(
                    course = course[0][3],
                    requests = [get_jwt_identity()]
                ).save()
                return(jsonify({'message': 'Solicitud enviada!'}), 200)

@app.route('/editSerial/<course>', methods=['PUT'])
@jwt_required
def edit_serial(course):            # Ruta para cambio de FOLIO 
    if(request.method=='PUT'):
        data = request.get_json()
        course = Course.objects.get(courseName=course)
        course['serial'] = data['serial']
        course.save()
        return(jsonify({'message': 'Cambios guardados!'}), 200)

@app.route('/teachers', methods=['GET', 'POST'])
# @jwt_required
def teachers():                     # Ruta para agregar un docente o consultar todos
    if (request.method == 'GET'):
        all_teachers = Teacher.objects.all()
        return(jsonify(all_teachers), 200)
    elif (request.method == 'POST'):
        data = request.get_json()
        try:
            departament = Departament.objects.get(name=data['departament'])
            try:
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
            except:
                return(jsonify({'message': 'Docente previamente registrado'}), 401)
            return(jsonify({'message': 'Docente agregado'}), 200)
        except:
            return(jsonify({'message': 'Departamento invalido'}), 404)

@app.route('/teacher/<rfc>', methods=['GET', 'PUT', 'DELETE'])
# @jwt_required
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
        teacher.save()
        return(jsonify({'message': 'Datos guardados.'}), 200)
    elif request.method == 'DELETE':
        advice = "{} eliminado".format(teacher.rfc)
        teacher.delete()
        return(jsonify({"message": advice}), 200)

@app.route('/changePassword', methods=['POST'])
@jwt_required
def change_password():          # No es necesario mencionar para que es, con el puro nombre de la funcion se ve
    if(request.method=='POST'):
        data = request.get_json()
        teacher = Teacher.objects.get(rfc=get_jwt_identity())
        if(sha256.verify(data['pin'], teacher['pin'])):
            teacher['pin'] = sha256.hash(data['newPin'])
            teacher.save()
            return(jsonify({'message': 'Clave actualizada!'}), 200)
        else:
            return(jsonify({'message': 'Clave previa incorrecta'}), 401)

@app.route('/myCourses', methods=['GET'])
@jwt_required
def my_courses():                    # Regresa todos los cursos en los que se ha registrado el docente
    if(request.method == 'GET'):
        courses = Course.objects.filter(teachersInCourse__contains=get_jwt_identity()).values_list('courseName')
        if len(courses) > 0:
            _mycourses = []
            for val in courses:
                _mycourses.append(val)
            return(jsonify({'message': _mycourses}), 200)
        else:
            return(jsonify({'message': 'No esta registrado en ningun curso'}), 404)

@app.route('/courses/coursesList', methods=['GET'])
# @jwt_required
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
@jwt_required
def assistantList_view(name):       # Ruta que regresa el PDF con la lista de asistencia del curso seleccionado POR PARAMETRO EN RUTA
    if(request.method=='GET'):################################################################# NO MOVERLE
        try:
            course = Course.objects.get(courseName=name)
        except Course.DoesNotExist:
            return(jsonify({"message": "Curso inexistente"}), 404)
        if(course['teachersInCourse']!=['No hay docentes registrados']):
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
        else:
            return(jsonify({'message': 'No hay docentes registrados'}), 404)

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
            
@app.route('/dataConcentrated', methods=['GET'])
def data_con():
    if(request.method=='GET'):
        # Nombres de los cursos
        depName = []
        totaldepTeacherNum = 0
        departaments = Departament.objects.all()
        for departament in departaments:
            depName.append(departament['name'])
        depName.remove('Desarrollo Académico')
        # Docentes por departamento
        depTeacherNum = []
        for val in depName:
            teacher = Teacher.objects.filter(departament=val)
            depTeacherNum.append(len(teacher))
            totaldepTeacherNum += len(teacher)
        depTeacherNum.append(totaldepTeacherNum)
        # Docentes que tomaron capacitacion docente
        depDocenteNum = [0, 0, 0, 0, 0, 0]
        rfcsCourse = Course.objects.filter(typeCourse='Docente').values_list('teachersInCourse')
        for rfcs in rfcsCourse:
            for rfc in rfcs:
                getDep = Teacher.objects.filter(rfc=rfc).values_list('departament')
                if(getDep[0]=='Ciencias Básicas'):
                    depDocenteNum[0]+=1
                elif(getDep[0]=='Económico-Administrativo'):
                    depDocenteNum[1]+=1
                elif(getDep[0]=='Ingenierías'):
                    depDocenteNum[2]+=1                    
                elif(getDep[0]=='Ingeniería Industrial'):
                    depDocenteNum[3]+=1
                elif(getDep[0]=='Sistemas y Computación'):
                    depDocenteNum[4]+=1
                depDocenteNum[5]+=1
        # Porcentaje del departamento
        depPercentDocent = [0, 0, 0, 0, 0, 0]
        for val in range(0, len(depTeacherNum)):
            depPercentDocent[val] = "{0:.2f}%".format((depDocenteNum[val]*100)/depTeacherNum[val])
        # Docentes que tomaron actualizacion profesional
        depProfesionalNum = [0, 0, 0, 0, 0, 0]
        rfcsCourse = Course.objects.filter(typeCourse='Profesional').values_list('teachersInCourse')
        for rfcs in rfcsCourse:
            for rfc in rfcs:
                getDep = Teacher.objects.filter(rfc=rfc).values_list('departament')
                if(getDep[0]=='Ciencias Básicas'):
                    depProfesionalNum[0]+=1
                elif(getDep[0]=='Económico-Administrativo'):
                    depProfesionalNum[1]+=1
                elif(getDep[0]=='Ingenierías'):
                    depProfesionalNum[2]+=1                    
                elif(getDep[0]=='Ingeniería Industrial'):
                    depProfesionalNum[3]+=1
                elif(getDep[0]=='Sistemas y Computación'):
                    depProfesionalNum[4]+=1
                depProfesionalNum[5]+=1
        # Porcentaje del departamento
        depPercentProfesional = [0, 0, 0, 0, 0, 0]
        for val in range(0, len(depTeacherNum)):
            depPercentProfesional[val] = "{0:.2f}%".format((depProfesionalNum[val]*100)/depTeacherNum[val])
        # Docentes que tomaron ambas
        depDocentProfesionalNum = [0, 0, 0, 0, 0, 0]
        courseDocente = Course.objects.filter(typeCourse='Docente').values_list('teachersInCourse')
        courseProfesional = Course.objects.filter(typeCourse='Profesional').values_list('teachersInCourse')
        teachers = Teacher.objects.all()
        all_rfc = []
        for val in teachers:
            all_rfc.append(val['rfc'])
        rfcCourse_docente = []
        rfcCourse_profesional = []
        for rfcs in courseDocente:
            for val in rfcs:
                rfcCourse_docente.append(val)
        for rfcs in courseProfesional:
            for val in rfcs:
                rfcCourse_profesional.append(val)
        for rfc in all_rfc:
            if(rfc in rfcCourse_docente and rfc in rfcCourse_profesional):
                depa = Teacher.objects.filter(rfc=rfc).values_list('departament')
                if(depa[0]=='Ciencias Básicas'):
                    depDocentProfesionalNum[0]+=1
                elif(depa[0]=='Económico-Administrativo'):
                    depDocentProfesionalNum[1]+=1
                elif(depa[0]=='Ingenierías'):
                    depDocentProfesionalNum[2]+=1                    
                elif(depa[0]=='Ingeniería Industrial'):
                    depDocentProfesionalNum[3]+=1
                elif(depa[0]=='Sistemas y Computación'):
                    depDocentProfesionalNum[4]+=1
                depDocentProfesionalNum[5]+=1
        # Porcentaje del departamento
        depPercentDocentProf = [0, 0, 0, 0, 0, 0]
        for val in range(0, len(depTeacherNum)):
            depPercentDocentProf[val] = "{0:.2f}%".format((depDocentProfesionalNum[val]*100)/depTeacherNum[val])
        # Docentes que tomaron algun curso
        capacitados = [0, 0, 0, 0, 0, 0]
        for rfc in all_rfc:
            department = Teacher.objects.filter(rfc=rfc).values_list('departament')
            isInCourse = Course.objects.filter(teachersInCourse__contains=rfc)
            if(len(isInCourse)>0):
                if(department[0]=='Ciencias Básicas'):
                    capacitados[0]+=1
                elif(department[0]=='Económico-Administrativo'):
                    capacitados[1]+=1
                elif(department[0]=='Ingenierías'):
                    capacitados[2]+=1                    
                elif(department[0]=='Ingeniería Industrial'):
                    capacitados[3]+=1
                elif(department[0]=='Sistemas y Computación'):
                    capacitados[4]+=1
                capacitados[5]+=1
        # Porcentaje del departamento
        depPercentYesCoursed = []
        for val in range(0, len(depTeacherNum)):
            depPercentYesCoursed.append("{0:.2f}%".format((capacitados[val]*100)/depTeacherNum[val]))
        # Docentes que no tomaron nada
        noCapacitados = []
        for val in range(0, len(depTeacherNum)):
            noCapacitados.append(depTeacherNum[val]-capacitados[val])
        # Porcentaje del departamento
        depPercentNoCoursed = []
        for val in range(0, len(depTeacherNum)):
            depPercentNoCoursed.append("{0:.2f}%".format((noCapacitados[val]*100)/depTeacherNum[val]))
        # Cursos de Capacitación Docente y Actualización Profesional
        numOfCD = Course.objects.filter(typeCourse='Docente')
        numOfAP = Course.objects.filter(typeCourse='Profesional')
        totalCourses = [len(numOfCD), len(numOfAP)]
        return(concentrated(depName, depTeacherNum, depDocenteNum, depPercentDocent, depProfesionalNum, depPercentProfesional, depDocentProfesionalNum, depPercentDocentProf, capacitados, depPercentYesCoursed, noCapacitados, depPercentNoCoursed, totalCourses), 200)

#  ==> --> In Develop <-- <==

# Example of route with JWT 
@app.route('/pull')
@jwt_required
def pull():
    return jsonify({"message": "Hello {}".format(get_jwt_identity())})

@app.route('/addTeacherinCourse/<course_name>', methods=['POST'])
def addTeacherinCourse_view(course_name):       # Ruta para agregar al docente aceptado al curso seleccionado
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(courseName=course_name)   # Obtiene la informacion del curso seleccionado
        except Course.DoesNotExist:
            return(jsonify({"message": "Curso inexistente"}), 404)
        all_rfc = Teacher.objects.filter(rfc__ne=course['teacherRFC']).values_list('rfc')   # Obtiene todos los RFC de los docentes excepto el docente que imparte el curso
        # restOfcourses = Course.objects.filter(courseName__ne=course_name).values_list('teachersInCourse', 'courseName') # Obtiene las listas de docentes de los demas cursos
        if(data['rfc'] not in all_rfc): # Verifica que exista el RFC                                   
            return(jsonify({'message': 'RFC invalido.'}), 401)
        else:   # En caso de que SI exista...
            if(data['rfc'] in course['teachersInCourse']):  # Verifica que el docente ya esta en la lista
                return(jsonify({"message": "Docente agregado previamente."}), 200)
            else:   # Si no...
                # hoursCourseOne = course['timetable'].split('-')  # Una marihuanada
                # if len(courseWillTeach)>0:
                #     if(courseWillTeach[0][1] <= course['dateStart'] <= courseWillTeach[0][2] or courseWillTeach[0][1] <= course['dateEnd'] <= courseWillTeach[0][2]):
                #         hoursCourseTwo = courseWillTeach[0][0].split('-')
                #         if(hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1] or hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]):
                #             return(jsonify({'message': 'Se empalma con la materia que imparte'}), 201)  
                # for rfcsCourse in restOfcourses: # Itera sobre el array que contiene los array de docentes de cada curso
                #     if data['rfc'] in rfcsCourse[0]:   # Si el docente ya esta en un curso...
                #         coursesData = Course.objects.filter(teachersInCourse=rfcsCourse[0], courseName=rfcsCourse[1]).values_list('timetable', 'dateStart', 'dateEnd', 'courseName') # Obtiene los datos del curso
                #         hoursCourseTwo = coursesData[0][0].split('-')   # Otra marihuanada
                #         if (coursesData[0][1] <= course['dateStart'] <= coursesData[0][2]) or (coursesData[0][1] <= course['dateEnd'] <= coursesData[0][2]): # Verifica que las fechas sean distintas, si no lo son...
                #             """La condicion de abajo verifica las marihuanadas que hice, o sea, que la hora de inicio y 
                #             finalizacion del curso, no este entre las horas de otro de inicio y finalizacion del curso"""
                #             if (hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1]) or (hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]): 
                #                 return jsonify({'message': 'Se empalma con otro curso a tomar'})
                courseRequest = RequestCourse.objects.get(course=course['courseName'])
                if data['rfc'] in courseRequest['requests']:
                    courseRequest['requests'].remove(data['rfc'])
                    courseRequest.save()
                else: 
                    return(jsonify({'message': 'No ha solicitado curso'}), 401)
                if(len(courseRequest['requests'])==0):
                    courseRequest.delete()  
                if(course['teachersInCourse'] == ["No hay docentes registrados"]):
                    course['teachersInCourse'] = []
                course['teachersInCourse'].append(data['rfc'])
                course.save()
                return(jsonify({'message': 'Docente agregado con exito.'}), 200)

@app.route('/rejectTeacherOfCourse/<name>', methods=['POST'])
def rejectTeacherOfCourse_view(name):       # Ruta que elimina el RFC del docente rechazado del curso
    if(request.method == 'POST'):
        data = request.get_json()
        courseRequest = RequestCourse.objects.get(course=name)
        if(data['rfc'] in courseRequest['requests']):
            courseRequest['requests'].remove(data['rfc'])
            courseRequest.save()
            if(len(courseRequest['requests'])==0):
                courseRequest.delete()
            try:
                blacklist = BlacklistRequest.objects.get(course=name)
                blacklist['requests'].append(data['rfc'])
                blacklist.save()
            except:
                BlacklistRequest(
                    course=name,
                    requests=[data['rfc']]
                ).save()
            return(jsonify({'message': "Rechazado, asi como ella me rechazo a mi :'v"}), 201)
        else:
            return(jsonify({'message': 'RFC inexistente'}), 500)

@app.route('/removeTeacherinCourse/<name>', methods=['POST'])
def removeTeacherinCourse_view(name):   # Ruta que elimina al docente del curso 
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(courseName=name)
        except Course.DoesNotExist:
            return(jsonify({"message": "Curso inexistente"}), 401)
        if(data['rfc'] in course['teachersInCourse']):
            course['teachersInCourse'].remove(data['rfc'])
            if not course['teachersInCourse']:
                course['teachersInCourse'] = ['No hay docentes registrados'] # La lista no debe estar vacia, porque lo toma como nulo y se borra el atributo del documento
            course.save()
            return(jsonify({"message": "Docente dado de baja exitosamente"}), 200)
        else:
            return(jsonify({"message": "No existe en la lista"}), 401)

@app.route('/addInfo', methods=['GET', 'POST'])
def addinfoView():                      # Only works to add meta data for each letterhead, next change will update meta data
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
        return(jsonify({"message": "Added"}), 200)

@app.route('/departament', methods=['GET', 'POST'])
def adddepaView():                      # Only works to add departament info for each letterhead, next change will update departament info
    if(request.method == 'GET'):
        info = Departament.objects.all()
        return jsonify(info)
    elif(request.method == 'POST'):
        data = request.get_json()
        Departament(
            name = data["name"],
            boss = data["boss"]
        ).save()
        return(jsonify({"message": "Added"}), 200)

@app.route('/departament/<name>', methods=['PUT'])
def departament_view(name):
    try:
        dep = Departament.objects.get(name=name)
        data=request.get_json()
    except:
        return(jsonify({'message': "Don't exists"}), 404)
    if(request.method=='PUT'):
        dep['name'] = data['name']
        dep['boss'] = data['boss']
        dep.save()
        return(jsonify({'message': 'Success!'}), 200)

@app.errorhandler(404)
def page_not_found(error):
    error = {
        "errorType": "404",
        "message": "Pagina no encontrada"
    }
    return(jsonify(error), 404)
