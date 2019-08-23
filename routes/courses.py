from models import Course, Teacher, RequestCourse, BlacklistRequest
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime as dt, timedelta as td
from mongoengine import errors as e
from flask import jsonify, request
from app import app, redis
from marsh import *

def periodOfTime(initDate, endDate):
    return 'Del {} al {} de {} del {}'.format(initDate.day, endDate.day, months[endDate.month-1], endDate.year) if initDate.month==endDate.month else 'Del {} de {} al {} de {} del {}'.format(initDate.day, months[initDate.month-1], endDate.day, months[endDate.month-1], endDate.year) if initDate.year==endDate.year else 'Del {} de {} del {} al {} de {} del {}'.format(initDate.day, months[initDate.month-1], initDate.year, endDate.day, months[endDate.month-1], endDate.year)

months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

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

@app.route('/getYears', methods=['GET'])
@jwt_required
def get_years():
    if request.method == 'GET':
        all_courses = Course.objects.filter().values_list('dateStart')
        years = []
        for course in all_courses:
            year = course.year
            if year not in years:
                years.append(year)
        return jsonify({'years': years})

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
        qualifieds = Qualified.objects.filter(course=name).values_list('approved', 'failed')
        newDictToSend = datos[0]
        try:
            newDictToSend['qualified'] = 'Aprobado' if (rfc in qualifieds[0][0]) else 'Reprobado' if (rfc in qualifieds[0][1]) else 'Sin calificar'
        except:
            newDictToSend['qualified'] = 'Sin calificar'
        limitDays = int(redis.get('days').decode('utf-8'))
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

@app.route('/editSerial/<course>', methods=['PUT'])
@jwt_required
def edit_serial(course):            # Ruta para cambio de FOLIO 
    if(request.method=='PUT'):
        data = request.get_json()
        course = Course.objects.get(courseName=course)
        course['serial'] = data['serial']
        course.save()
        return(jsonify({'message': 'Cambios guardados!'}), 200)
