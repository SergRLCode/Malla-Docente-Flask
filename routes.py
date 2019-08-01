from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
from models import Course, Teacher, LetterheadMetaData, Qualified, BlacklistJWT, RequestCourse, BlacklistRequest
from pdfs import assistantList, coursesList, inscription, pollDocument, concentrated
from datetime import datetime as dt, timedelta as td
from flask import jsonify, request, make_response
from passlib.hash import pbkdf2_sha256 as sha256
from mongoengine import errors as e
from reportlab.pdfgen import canvas
from app import app, jwt, redis
from marsh import *
from auth import *

months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def periodOfTime(initDate, endDate):
    return 'Del {} al {} de {} del {}'.format(initDate.day, endDate.day, months[endDate.month-1], endDate.year) if initDate.month==endDate.month else 'Del {} de {} al {} de {} del {}'.format(initDate.day, months[initDate.month-1], endDate.day, months[endDate.month-1], endDate.year) if initDate.year==endDate.year else 'Del {} de {} del {} al {} de {} del {}'.format(initDate.day, months[initDate.month-1], initDate.year, endDate.day, months[endDate.month-1], endDate.year)

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

@app.route('/logoutA', methods=['GET'])
@jwt_required
def logout_user():                  # Un logout que agrega el ID del JWT de acceso en una coleccion para evitar el uso de este JWT 
    _jwt = get_raw_jwt()['jti']
    _rfc = get_jwt_identity()[0]
    BlacklistJWT(
        jwt = _jwt,
        identity = _rfc
    ).save()
    return(jsonify({'message': 'Bye bye!'}), 200)

@app.route('/courses', methods=['GET', 'POST'])
@jwt_required
def courses():                      # Ruta para agregar un curso o consultar todos
    if (request.method == 'GET'):
        all_courses = Course.objects.all()
        data = courseSchemas.dump(all_courses)
        for course in data[0]:
            period = dt.strptime(course['dateStart'].replace("T00:00:00+00:00", ""), "%Y-%m-%d")
            if months[period.month-1]=="Julio":
                period = "{} {}".format("{}-{}".format(months[period.month-1], months[period.month]), period.year)
            elif months[period.month-1]=="Agosto":
                period = "{} {}".format("{}-{}".format(months[period.month-2], months[period.month-1]), period.year)
            else:
                period = "{} {}".format(months[period.month-1], period.year)
            course['period'] = period
            teacherName = Teacher.objects.filter(rfc=course['teacherRFC']).values_list('name', 'fstSurname', 'sndSurname')
            course['teacher'] = "{} {} {}".format(teacherName[0][0], teacherName[0][1], teacherName[0][2])
        return(jsonify(data), 200)
    elif (request.method == 'POST'):
        data = request.get_json()
        all_rfc = Teacher.objects.all().values_list('rfc')
        totalDays = (dt.strptime(data['dateEnd'], "%Y-%m-%d")-dt.strptime(data['dateStart'], "%Y-%m-%d")).days+1
        hours = data['timetable'].replace(":00", "").split('-')
        totalHrs = totalDays*(int(hours[1])-int(hours[0]))
        if totalHrs <= 0 or totalHrs > 40:
            return(jsonify({'message': 'Verifique bien las fechas y horas'}), 400)
        if data['teacherRFC'] not in all_rfc:
            return(jsonify({"message": "Error, RFC no valido."}), 404)
        try:
            Course.objects.get(courseName=data["courseName"])
            return(jsonify({"message": "Curso ya esta registrado."}), 400)
        except:
            Course(
                courseName = data["courseName"],
                teacherRFC = data["teacherRFC"],
                modality = data["modality"],
                dateStart = data["dateStart"],
                dateEnd = data["dateEnd"],
                timetable = data["timetable"],
                place = data["place"],
                description = data["description"],
                courseTo = data["courseTo"],
                typeCourse = data["typeCourse"],
                teachersInCourse = ['No hay docentes registrados'],
                totalHours = totalHrs,
                serial = ""
            ).save()
            return(jsonify({"message": "Curso guardado."}), 200)

@app.route('/periods', methods=['GET'])
@jwt_required
def periodsOfSystem():
    if(request.method=='GET'):
        all_courses = Course.objects.filter().values_list('dateStart')
        periods = []
        for course in all_courses:
            if months[course.month-1]=="Julio":
                period = "{} {}".format("{}-{}".format(months[course.month-1], months[course.month]), course.year)
            elif months[course.month-1]=="Agosto":
                period = "{} {}".format("{}-{}".format(months[course.month-2], months[course.month-1]), course.year)
            else:
                period = "{} {}".format(months[course.month-1], course.year)
            if period not in periods:
                periods.append(period)
        return(jsonify({'message': periods}), 200)

@app.route('/coursesByPeriod/<period>', methods=['GET'])
@jwt_required
def courses_by_period(period):
    if(request.method=='GET'):
        all_courses = Course.objects.filter().values_list('dateStart', 'courseName', 'teacherRFC', 'timetable')
        coursesToSend = []
        periodDesglosado = period.split(' ')
        if periodDesglosado[0] == 'Julio-Agosto':
            mesesDesglosados = periodDesglosado[0].split('-')
            listaQueContieneMesesAndYear = [months.index(mesesDesglosados[0])+1, months.index(mesesDesglosados[1])+1, int(periodDesglosado[1])]
            for course in all_courses:
                if course[0].year == listaQueContieneMesesAndYear[2]:
                    if course[0].month == listaQueContieneMesesAndYear[0] or course[0].month == listaQueContieneMesesAndYear[1]:
                        teacher = Teacher.objects.filter(rfc=course[2]).values_list('name', 'fstSurname', 'sndSurname')
                        coursesToSend.append([course[1], "{} {} {}".format(teacher[0][0], teacher[0][1], teacher[0][2]), course[3]])
        else:
            listaQueContieneMesesAndYear = [months.index(periodDesglosado[0])+1, int(periodDesglosado[1])]
            for course in all_courses:
                if course[0].year == listaQueContieneMesesAndYear[1]:
                    if course[0].month == listaQueContieneMesesAndYear[0] or course[0].month == listaQueContieneMesesAndYear[1]:
                        teacher = Teacher.objects.filter(rfc=course[2]).values_list('name', 'fstSurname', 'sndSurname')
                        coursesToSend.append([course[1], "{} {} {}".format(teacher[0][0], teacher[0][1], teacher[0][2]), course[3]])
        return jsonify({'courses': coursesToSend})

@app.route('/availableCourses', methods=['GET'])
@jwt_required
def available_courses():            # Ruta que retorna una lista con los cursos disponibles, siendo el dia de inicio mayor a la fecha del servidor
    if(request.method=='GET'):
        _rfc = ""
        availableCourses = Course.objects.filter(dateStart__gte=dt.now().date()).values_list('courseName', 'teacherRFC', 'timetable', 'teachersInCourse', 'state')
        if get_jwt_identity()[1] != 0 and get_jwt_identity()[1] != 1:
            myCourses = Course.objects.filter(teacherRFC=get_jwt_identity()[0]).values_list('courseName')
            coursesRequested = RequestCourse.objects.filter(requests__contains=get_jwt_identity()[0]).values_list('course')
            coursesRejected = BlacklistRequest.objects.filter(requests__contains=get_jwt_identity()[0]).values_list('course')
            _rfc = get_jwt_identity()[0]
        else:
            myCourses = []
            coursesRejected = []
            coursesRequested = []
        arrayToSend = []
        for vals in availableCourses:
            if _rfc not in vals[3] and vals[0] not in coursesRequested and vals[0] not in coursesRejected and vals[0] not in myCourses:
                teacherName = Teacher.objects.filter(rfc=vals[1]).values_list('name', 'fstSurname', 'sndSurname')
                completeName = "{} {} {}".format(teacherName[0][0], teacherName[0][1], teacherName[0][2])
                arrayToSend.append({
                    'courseName': vals[0],
                    'teacherName': completeName, 
                    'timetable': vals[2], 
                    'state': vals[4]
                })
        return(jsonify({'courses': arrayToSend}), 200)

@app.route('/course/<name>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def course(name):                   # Ruta para consultar uno en especifico, editar info de un curso en especifico o borrar ese curso en especifico
    try:
        course = Course.objects.get(courseName=name)
    except Course.DoesNotExist:
        return(jsonify({"message": "Don't exists"}), 404)
    if (request.method == 'GET'):################################################### Ya no moverle
        datos = courseSchema.dump(course)
        limitDays = int(redis.get('days').decode('utf-8'))
        newDictToSend = datos[0]
        endDay = dt.strptime(datos[0]['dateEnd'].replace("T00:00:00+00:00", ""), "%Y-%m-%d")
        del newDictToSend['id']
        keyOfRedis = name.replace(" ", "_").lower()
        listRedisLen = redis.llen(keyOfRedis)
        if newDictToSend['state'] == 'Terminado' and dt.now().date() < endDay.date()+td(days=limitDays):
            newDictToSend['allowPoll'] = True
            newDictToSend['leftDays'] = (endDay.date()+td(days=limitDays)-dt.now().date()).days
            newDictToSend['teachersThatHaveDoneThePoll'] = [val.decode('utf-8') for val in redis.lrange(keyOfRedis, 0, listRedisLen)]
        else:
            newDictToSend['allowPoll'] = False
        teacherWillteach = Teacher.objects.filter(rfc=course['teacherRFC']).values_list("name", "fstSurname", "sndSurname")
        newDictToSend['teacherName'] = "{} {} {}".format(teacherWillteach[0][0], teacherWillteach[0][1], teacherWillteach[0][2])
        return(jsonify(newDictToSend), 200)
    elif (request.method == 'PUT'):################################################# Ya no moverle
        data = request.get_json()
        totalDays = (dt.strptime(data['dateEnd'], "%Y-%m-%d")-dt.strptime(data['dateStart'], "%Y-%m-%d")).days+1
        hours = data['timetable'].replace(":00", "").split('-')
        totalHrs = totalDays*(int(hours[1])-int(hours[0]))
        attributes = ("courseName", "courseTo", "place", "description", "dateStart", "dateEnd", "modality", "timetable", "typeCourse")
        all_rfc = Teacher.objects.all().values_list('rfc')        
        for attribute in attributes:
            course[attribute] = data[attribute]
        if data['teacherRFC'] in all_rfc:
            course['teacherRFC'] = data['teacherRFC']
            course['totalHours'] = totalHrs
        else:
            return(jsonify({'message': 'RFC invalido'}), 404)
        if totalHrs <= 0 or totalHrs > 40:
            return(jsonify({'message': 'Verifique bien las fechas y horas'}), 400)            
        course.save()
        return(jsonify({'message': 'Cambios guardados.'}), 200)
    elif (request.method == 'DELETE'):############################################### Ya no moverle
        advice = "Curso {} eliminado".format(course.courseName)
        course.delete()
        return(jsonify({"message": advice}), 200)

@app.route('/teacherListToQualify/<course>', methods=['GET'])
@jwt_required
def teacher_list_to_qualify(course):
    if request.method == 'GET':
        try:
            course = Course.objects.get(courseName=course)
        except:
            return jsonify({'message': "Don't exists"}), 404
        teacherList = []
        qualified = Qualified.objects.filter(course=course['courseName']).values_list('approved', 'failed')
        if(len(qualified)!=0):
            for val in course['teachersInCourse']:
                if val not in qualified[0][0] and val not in qualified[0][1]:
                    teacherData = Teacher.objects.filter(rfc=val).values_list('name', 'fstSurname', 'sndSurname')
                    teacherList.append({
                        'rfc': val,
                        'name': "{} {} {}".format(teacherData[0][0], teacherData[0][1], teacherData[0][2])
                    })
        else:
            for val in course['teachersInCourse']:
                teacherData = Teacher.objects.filter(rfc=val).values_list('name', 'fstSurname', 'sndSurname')
                teacherList.append({
                    'rfc': val,
                    'name': "{} {} {}".format(teacherData[0][0], teacherData[0][1], teacherData[0][2])
                })
        return jsonify({'teachers': teacherList}), 200

@app.route('/teacherList/<course>', methods=['GET'])
@jwt_required
def teacher_list(course):
    if request.method == 'GET':
        try:
            course = Course.objects.get(courseName=course)
        except:
            return jsonify({'message': "Don't exists"}), 404
        teacherList = []
        for val in course['teachersInCourse']:
            teacherData = Teacher.objects.filter(rfc=val).values_list('name', 'fstSurname', 'sndSurname')
            teacherList.append({
                'rfc': val,
                'name': "{} {} {}".format(teacherData[0][0], teacherData[0][1], teacherData[0][2])
            })
        return jsonify({'teachers': teacherList}), 200

@app.route('/courseRequest/<name>', methods=['GET', 'POST'])
@jwt_required
def course_request(name):           # Ruta en la cual el docente agrega su RFC para peticion de tomar un curso
    if request.method == 'GET':
        course = Course.objects.filter(courseName=name).values_list('timetable', 'dateStart', 'dateEnd', 'courseName', 'teacherRFC')
        courseWillTeach = Course.objects.filter(teacherRFC=get_jwt_identity()[0]).values_list('timetable', 'dateStart', 'dateEnd', 'courseName', 'teacherRFC')
        if len(course) == 0:                                                        # checa si existe el curso
            return(jsonify({'message': "Curso inexistente"}), 401)
        else:                                                                       # NOTA: preguntar hasta cuando se puede solicitar un curso
            if(course[0][4]==get_jwt_identity()[0]):
                return(jsonify({'message': 'Usted imparte el curso'}), 401)    
            else:
                try:
                    courseInRequest = RequestCourse.objects.get(course=course[0][3])
                    if get_jwt_identity()[0] not in courseInRequest['requests']:
                        if len(courseWillTeach)>0:
                            if(courseWillTeach[0][1] <= course[0][1] <= courseWillTeach[0][2] or courseWillTeach[0][1] <= course[0][2] <= courseWillTeach[0][2]):
                                hoursCourseOne = course[0][0].split('-')  # Una marihuanada
                                hoursCourseTwo = courseWillTeach[0][0].split('-')
                                if(hoursCourseOne[0] <= hoursCourseTwo[0] < hoursCourseOne[1] or hoursCourseOne[0] <= hoursCourseTwo[1] < hoursCourseOne[1]):
                                    return(jsonify({'message': 'Se empalma con la materia que imparte'}), 401)  
                        courseInRequest["requests"].append(get_jwt_identity()[0])
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
                        requests = [get_jwt_identity()[0]]
                    ).save()
                    return(jsonify({'message': 'Solicitud enviada!'}), 200)
    if request.method == 'POST':
        data = request.get_json()
        try:
            courseInRequest = RequestCourse.objects.get(course=name)
            courseInRequest["requests"].append(data['rfc'])
            courseInRequest.save()
        except:
            RequestCourse(
                course = name,
                requests = [data['rfc']]
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

@app.route('/myCourses', methods=['GET'])
@jwt_required
def my_courses():                    # Regresa todos los cursos en los que se ha registrado el docente
    if(request.method == 'GET'):
        courses = Course.objects.filter(teachersInCourse__contains=get_jwt_identity()[0]).values_list('courseName', 'timetable', 'teacherRFC', 'state')
        _mycourses = []
        if len(courses) > 0:
            for val in courses:
                teacherName = Teacher.objects.filter(rfc=val[2]).values_list('name', 'fstSurname', 'sndSurname')
                _mycourses.append({
                    'courseName': val[0],
                    'timetable': val[1],
                    'teacherName': "{} {} {}".format(teacherName[0][0], teacherName[0][1], teacherName[0][2]),
                    'state': val[3]
                })
            return(jsonify({'courses': _mycourses}), 200)
        else:
            return(jsonify({'message': 'No esta registrado en ningun curso'}), 404)

@app.route('/myCoursesWillTeach', methods=['GET'])
@jwt_required
def my_courses_will_teach():
    coursesWillTeach = []
    courses = Course.objects.filter(teacherRFC=get_jwt_identity()[0]).values_list('courseName', 'timetable', 'dateStart', 'dateEnd', 'state')
    for course in courses:
        coursesWillTeach.append({
            'courseName': course[0], 
            'timetable': course[1], 
            'duration': periodOfTime(course[2], course[3]),
            'state': course[4]
        })
    return jsonify({'courses': coursesWillTeach}), 200

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
        # courses = Course.objects.filter(teachersInCourse__contains=teacher.rfc)
        requests = RequestCourse.objects.filter(requests__contains=teacher.rfc)
        blacklist = BlacklistRequest.objects.filter(requests__contains=teacher.rfc)
        # for course in courses:
        #     course['teachersInCourse'].remove(rfc)
        #     if not course['teachersInCourse']:
        #         course['teachersInCourse'] = ['No hay docentes registrados'] # La lista no debe estar vacia, porque lo toma como nulo y se borra el atributo del documento
        #     course.save()
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
def teachersByDep(course):
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

@app.route('/requestsTo/<name>')
@jwt_required
def requests_to(name):
    try:
        requests = RequestCourse.objects.get(course=name)
    except:
        arrayToSend = []
        return jsonify(arrayToSend), 200
    else:
        arrayToSend = []
        for val in requests['requests']:
            teacherName = Teacher.objects.filter(rfc=val).values_list('name', 'fstSurname', 'sndSurname')
            arrayToSend.append({
                'rfc': val,
                'name': "{} {} {}".format(teacherName[0][0], teacherName[0][1], teacherName[0][2])
            })
        return jsonify(arrayToSend), 200

@app.route('/addTeacherinCourse/<course_name>', methods=['POST'])
@jwt_required
def addTeacherinCourse_view(course_name):       # Ruta para agregar al docente aceptado al curso seleccionado
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            course = Course.objects.get(courseName=course_name)   # Obtiene la informacion del curso seleccionado
        except Course.DoesNotExist:
            return(jsonify({"message": "Curso inexistente"}), 404)
        all_rfc = Teacher.objects.filter(rfc__ne=course['teacherRFC']).values_list('rfc')   # Obtiene todos los RFC de los docentes excepto el docente que imparte el curso
        if(data['rfc'] not in all_rfc): # Verifica que exista el RFC                                   
            return(jsonify({'message': 'Pa empezar ni existe xd.'}), 401)
        else:   # En caso de que SI exista...
            if(data['rfc'] in course['teachersInCourse']):  # Verifica que el docente ya esta en la lista
                return(jsonify({"message": "Docente agregado previamente."}), 200)
            else:   # Si no...
                try:
                    courseRequest = RequestCourse.objects.get(course=course['courseName'])
                except:
                    return jsonify({'message': 'Peticion invalida'}), 404
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
@jwt_required
def rejectTeacherOfCourse_view(name):       # Ruta que elimina el RFC del docente rechazado del curso
    if(request.method == 'POST'):
        data = request.get_json()
        try:
            courseRequest = RequestCourse.objects.get(course=name)
        except:
            return jsonify({'message': 'Peticion invalida'}), 404
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

@app.route('/removeTeacherinCourse/<name>', methods=['GET', 'POST'])
@jwt_required
def removeTeacherinCourse_view(name):   # Ruta que elimina al docente del curso 
    try:
        course = Course.objects.get(courseName=name)
    except Course.DoesNotExist:
        return(jsonify({"message": "Curso inexistente"}), 401)
    if (request.method == 'GET'):
        if(get_jwt_identity()[0] in course['teachersInCourse']):
            course['teachersInCourse'].remove(get_jwt_identity()[0])
            if not course['teachersInCourse']:
                course['teachersInCourse'] = ['No hay docentes registrados'] # La lista no debe estar vacia, porque lo toma como nulo y se borra el atributo del documento
            course.save()
            return(jsonify({"message": "Docente dado de baja exitosamente"}), 200)
        else:
            return(jsonify({"message": "No existe en la lista"}), 401)
    elif(request.method == 'POST'):
        data = request.get_json()
        if(data['rfc'] in course['teachersInCourse']):
            course['teachersInCourse'].remove(data['rfc'])
            if not course['teachersInCourse']:
                course['teachersInCourse'] = ['No hay docentes registrados'] # La lista no debe estar vacia, porque lo toma como nulo y se borra el atributo del documento
            course.save()
            return(jsonify({"message": "Docente dado de baja exitosamente"}), 200)
        else:
            return(jsonify({"message": "No existe en la lista"}), 401)

@app.route('/approvedCourse/<name>', methods=['GET', 'PUT'])
@jwt_required
def teacherApprovedCourse(name):
    if(request.method == 'GET'):
        try:
            qualified = Qualified.objects.get(course=name)
            return jsonify({'approved': qualified['approved']})
        except:
            return(jsonify({"message": "No hay aprobados aun"}), 404)
    elif(request.method == 'PUT'):
        data = request.get_json()
        try:
            course = Course.objects.get(courseName=name)
        except:
            return jsonify({'message': "Don't exists"}), 400
        try:
            qualified = Qualified.objects.get(course=course['courseName'])
            if data['rfc'] in course['teachersInCourse']:
                qualified['approved'].append(data['rfc'])
                qualified.save()
            else:
                return jsonify({"message": "Docente no registrado"}), 404
        except:
            if data['rfc'] in course['teachersInCourse']:
                Qualified(
                    course=course['courseName'], approved=[data['rfc']], failed=[]
                ).save()
            else:
                return jsonify({"message": "Docente no registrado"}), 404
        return jsonify({'message': 'Success!'}), 200

@app.route('/failedCourse/<name>', methods=['GET', 'PUT'])
@jwt_required
def teacherFailedCourse(name):
    if(request.method == 'GET'):
        try:
            qualified = Qualified.objects.get(course=name)
            return jsonify({'failed': qualified['failed']})
        except:
            return jsonify({"message": "No hay reprobados aun"}), 404
    elif(request.method == 'PUT'):
        data = request.get_json()
        try:
            course = Course.objects.get(courseName=name)
        except:
            return jsonify({'message': "Don't exists"}), 400
        try:
            qualified = Qualified.objects.get(course=course['courseName'])
            if data['rfc'] in course['teachersInCourse']:            
                qualified['failed'].append(data['rfc'])
                qualified.save()
            else:
                return jsonify({"message": "Docente no registrado"}), 404
        except:
            if data['rfc'] in course['teachersInCourse']:
                Qualified(
                    course=course['courseName'], approved=[], failed=[data['rfc']]
                ).save()
            else:
                return jsonify({"message": "Docente no registrado"}), 404
        return jsonify({'message': 'Success!'}), 200

@app.route('/getRequests', methods=['GET'])
@jwt_required
def get_Requests():
    if request.method == 'GET':
        list_of_courses = []
        allData = []
        myRequests = RequestCourse.objects.filter(requests__contains=get_jwt_identity()[0])
        for val in myRequests:
            list_of_courses.append(val['course'])
        for val in list_of_courses:
            _course_ = Course.objects.filter(courseName=val).values_list('courseName', 'teacherRFC', 'timetable')
            teacherData = Teacher.objects.filter(rfc=_course_[0][1]).values_list('name', 'fstSurname', 'sndSurname')
            allData.append({
                'name': _course_[0][0],
                'teacher': "%s %s %s" % (teacherData[0][0], teacherData[0][1], teacherData[0][2]),
                'timetable': _course_[0][2]
            })
        return jsonify({'courses': allData})

@app.route('/cancelRequest/<course>', methods=['GET'])
@jwt_required
def cancelRequest(course):
    if request.method == 'GET':
        try:
            _request = RequestCourse.objects.get(course=course)
        except:
            return jsonify({'message': "Don't exists"})
        else:
            _request['requests'].remove(get_jwt_identity()[0])
            _request.save()
            if(len(_request['requests'])==0):
                _request.delete()
            try:
                blacklist = BlacklistRequest.objects.get(course=course)
            except:
                BlacklistRequest(
                    course=course,
                    requests=[get_jwt_identity()[0]]
                ).save()
            else:
                blacklist['requests'].append(get_jwt_identity()[0])
                blacklist.save()
            return jsonify({'message': "Canceled"})
            
@app.route('/courses/coursesList', methods=['GET'])
@jwt_required
def coursesList_view():             # Ruta que regresa el documento PDF con lista de cursos disponibles 
    actualMonth = dt.now().month
    actualYear = dt.now().year
    all_courses = Course.objects.all()
    if len(all_courses)!=0:
        courses = []
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        for course in all_courses:
            teacherName = Teacher.objects.filter(rfc=course["teacherRFC"]).values_list("name", "fstSurname", "sndSurname")
            if course['dateStart'].year == actualYear:
                if course['dateStart'].month == 7 or course['dateStart'].month == 8 and (actualMonth == 7 or actualMonth == 8):
                    courses.append([
                        course["courseName"], course["description"], course["dateStart"], course["dateEnd"], course["place"],
                        "{} hrs.".format(course["totalHours"]),
                        "{} {} {}".format(teacherName[0][0], teacherName[0][1], teacherName[0][2]),
                        course["courseTo"]
                    ])
                elif course['dateStart'].month == actualMonth:
                    courses.append([
                        course["courseName"], course["description"], course["dateStart"], course["dateEnd"], course["place"],
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
        teacher = Teacher.objects.get(rfc=get_jwt_identity()[0])
        bossData = Teacher.objects.filter(position='Jefe de departamento', departament=teacher['departament']).values_list('name', 'fstSurname', 'sndSurname')
        bossName = "{} {} {}".format(bossData[0][0], bossData[0][1], bossData[0][2])
        if(teacher['rfc'] not in course['teachersInCourse']):
            teacherWillTeach = Teacher.objects.filter(rfc=course['teacherRFC']).values_list("name", "fstSurname", "sndSurname")
            return(inscription(teacher, bossName, course, teacherWillTeach), 200)
        else:
            return(jsonify({"message":"Ya esta en el curso"}), 401)

@app.route('/course/<name>/poll', methods=['POST'])
@jwt_required
def poll_view(name):                # Ruta que regresa el PDF con la encuesta contestada por el docente
    if(request.method == 'POST'):
        courseData = Course.objects.filter(courseName=name).values_list('courseName', 'teacherRFC', 'place', 'dateStart', 'dateEnd', 'totalHours', 'timetable', 'teachersInCourse')
        if len(courseData)!=0:
            if get_jwt_identity()[0] in courseData[0][7]:
                data = request.get_json()
                teacherThatTeach = Teacher.objects.filter(rfc=courseData[0][1]).values_list('name', 'fstSurname', 'sndSurname')
                departament = Teacher.objects.filter(rfc=get_jwt_identity()[0]).values_list('departament')
                keyOfRedis = name.replace(" ", "_").lower()
                listRedisLen = redis.llen(keyOfRedis)
                listRedis = [val.decode('utf-8') for val in redis.lrange(keyOfRedis, 0, listRedisLen)]
                redis.lpush(keyOfRedis, get_jwt_identity()[0])
                return(pollDocument(data, courseData, teacherThatTeach, departament[0]), 200)
            else:
                return(jsonify({'message': 'Curso no registrado.'}), 404)
        else:
            return(jsonify({'message': 'Curso inexistente.'}), 404)

@app.route('/establishLimitDaysOfPoll', methods=['PUT'])
@jwt_required
def establish_Limit_Days_Of_Poll():
    if request.method == 'PUT':
        data = request.get_json()
        if len(data.items())>1:
            return jsonify({'message': 'Pa que mandas mas keys? ggg salu2'}), 400
        for (key, val) in data.items():
            if val >= 0:
                redis.set(key, val)
            else:
                return jsonify({'message': 'Pa que mandas un numero negativo? ggg salu2'}), 400
        return jsonify({'message': 'Se ha establecido el limite de dias exitosamente'}), 200

@app.route('/dataConcentrated', methods=['GET'])
@jwt_required
def data_con():                         # Ruta que regresa un PDF con los datos de los cursos concentrados
    if(request.method=='GET'):
        # Nombres de los cursos
        depName = []
        totaldepTeacherNum = 0
        depas = Teacher.objects.filter().values_list('departament')
        for val in depas:
            if val not in depName:
                depName.append(val)
        if "" in depName:
            depName.remove("")
        if "Desarrollo Académico" in depName:
            depName.remove("Desarrollo Académico")
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
                try:
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
                except:
                    depDocenteNum = [0, 0, 0, 0, 0, 0]                    
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
                try:
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
                except:
                    depProfesionalNum = [0, 0, 0, 0, 0, 0]                                   
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

@app.errorhandler(404)
@jwt_required
def page_not_found(error):
    error = {"errorType": "404", "message": "Pagina no encontrada"}
    return(jsonify(error), 404)

#  ==> --> In Develop <-- <==