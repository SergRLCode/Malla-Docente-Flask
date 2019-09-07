from pdfs import assistantList, coursesList, inscription, pollDocument, concentrated, acreditation
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Course, Teacher, CourseSerialToDocument
from datetime import datetime as dt, timedelta as td
from flask import jsonify, request
from app import app, redis
from auth import *

def periodOfTime(initDate, endDate):
    return 'Del {} al {} de {} del {}'.format(initDate.day, endDate.day, months[endDate.month-1], endDate.year) if initDate.month==endDate.month else 'Del {} de {} al {} de {} del {}'.format(initDate.day, months[initDate.month-1], endDate.day, months[endDate.month-1], endDate.year) if initDate.year==endDate.year else 'Del {} de {} del {} al {} de {} del {}'.format(initDate.day, months[initDate.month-1], initDate.year, endDate.day, months[endDate.month-1], endDate.year)

months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

@app.route('/courses/coursesList', methods=['GET'])
@jwt_required
def coursesList_view():             # Ruta que regresa el documento PDF con lista de cursos disponibles 
    actualMonth = dt.now().month
    actualYear = dt.now().year
    all_courses = Course.objects.all()
    if len(all_courses)!=0:
        courses = []
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
                courseTeacher["rfc"],
                courseTeacher["curp"]
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

@app.route('/acreditation/<course>', methods=['GET'])
@jwt_required
def _acreditation(course):
    if request.method == 'GET':
        try:
            data = Teacher.objects.get(rfc=get_jwt_identity()[0])
        except:
            return jsonify({'message': "Don't exists"}), 404
        try:
            _course = Course.objects.get(courseName=course)
        except:
            return jsonify({'message': "Don't exists"}), 404
        count = int(redis.get('count').decode('utf-8'))
        _count = '00%s'%count if count<10 else '0%s'%count if count<100 else '%s'%count
        try:
            damnedData = CourseSerialToDocument.objects.get(course=course, rfc=get_jwt_identity()[0])
            damnedSerial = damnedData['serial']
        except:
            CourseSerialToDocument(
                course=course,
                rfc=get_jwt_identity()[0],
                serial='%s/%s'%(_count, dt.now().year)
            ).save()
            redis.set('count', count+1)
            damnedSerial = '%s/%s'%(_count, dt.now().year)
        someData = {
            'name': '%s %s %s'%(data['name'], data['fstSurname'], data['sndSurname']),
            'course': _course['courseName'],
            'serial': _course['serial'],
            'period': periodOfTime(_course['dateStart'], _course['dateEnd']).upper(),
            'duration': _course['totalHours'],
            'doc_serial': damnedSerial
        }
        return acreditation(someData)

@app.route('/dataConcentrated/<year>', methods=['GET'])
@jwt_required
def data_con(year):                         # Ruta que regresa un PDF con los datos de los cursos concentrados
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
        rfcsCourse = Course.objects.filter(typeCourse='Docente', dateStart__gte=dt.strptime('%s-01-01'%year, '%Y-%m-%d'), dateEnd__lte=dt.strptime('%s-12-31'%year, '%Y-%m-%d')).values_list('teachersInCourse')
        for rfcs in rfcsCourse:
            for rfc in rfcs:
                getDep = Teacher.objects.filter(rfc=rfc).values_list('departament')
                try:
                    if(getDep[0]=='Sistemas y Computación'):
                        depDocenteNum[0]+=1
                    elif(getDep[0]=='Ingenierías'):
                        depDocenteNum[1]+=1
                    elif(getDep[0]=='Ciencias Básicas'):
                        depDocenteNum[2]+=1                    
                    elif(getDep[0]=='Económico-Administrativo'):
                        depDocenteNum[3]+=1
                    elif(getDep[0]=='Ingeniería Industrial'):
                        depDocenteNum[4]+=1
                    depDocenteNum[5]+=1
                except:
                    continue
        # Porcentaje del departamento
        depPercentDocent = [0, 0, 0, 0, 0, 0]
        for val in range(0, len(depTeacherNum)):
            depPercentDocent[val] = "{0:.2f}%".format((depDocenteNum[val]*100)/depTeacherNum[val])
        # Docentes que tomaron actualizacion profesional
        depProfesionalNum = [0, 0, 0, 0, 0, 0]
        rfcsCourse = Course.objects.filter(typeCourse='Profesional', dateStart__gte=dt.strptime('%s-01-01'%year, '%Y-%m-%d'), dateEnd__lte=dt.strptime('%s-12-31'%year, '%Y-%m-%d')).values_list('teachersInCourse')
        for rfcs in rfcsCourse:
            for rfc in rfcs:
                getDep = Teacher.objects.filter(rfc=rfc).values_list('departament')
                try:
                    if(getDep[0]=='Sistemas y Computación'):
                        depProfesionalNum[0]+=1
                    elif(getDep[0]=='Ingenierías'):
                        depProfesionalNum[1]+=1
                    elif(getDep[0]=='Ciencias Básicas'):
                        depProfesionalNum[2]+=1                    
                    elif(getDep[0]=='Económico-Administrativo'):
                        depProfesionalNum[3]+=1
                    elif(getDep[0]=='Ingeniería Industrial'):
                        depProfesionalNum[4]+=1
                    depProfesionalNum[5]+=1
                except:
                    continue                                 
        # Porcentaje del departamento
        depPercentProfesional = [0, 0, 0, 0, 0, 0]
        for val in range(0, len(depTeacherNum)):
            depPercentProfesional[val] = "{0:.2f}%".format((depProfesionalNum[val]*100)/depTeacherNum[val])
        # Docentes que tomaron ambas
        depDocentProfesionalNum = [0, 0, 0, 0, 0, 0]
        courseDocente = Course.objects.filter(typeCourse='Docente', dateStart__gte=dt.strptime('%s-01-01'%year, '%Y-%m-%d'), dateEnd__lte=dt.strptime('%s-12-31'%year, '%Y-%m-%d')).values_list('teachersInCourse')
        courseProfesional = Course.objects.filter(typeCourse='Profesional', dateStart__gte=dt.strptime('%s-01-01'%year, '%Y-%m-%d'), dateEnd__lte=dt.strptime('%s-12-31'%year, '%Y-%m-%d')).values_list('teachersInCourse')
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
                if(depa[0]=='Sistemas y Computación'):
                    depDocentProfesionalNum[0]+=1
                elif(depa[0]=='Ingenierías'):
                    depDocentProfesionalNum[1]+=1
                elif(depa[0]=='Ciencias Básicas'):
                    depDocentProfesionalNum[2]+=1                    
                elif(depa[0]=='Económico-Administrativo'):
                    depDocentProfesionalNum[3]+=1
                elif(depa[0]=='Ingeniería Industrial'):
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
            isInCourse = Course.objects.filter(teachersInCourse__contains=rfc, dateStart__gte=dt.strptime('%s-01-01'%year, '%Y-%m-%d'), dateEnd__lte=dt.strptime('%s-12-31'%year, '%Y-%m-%d'))
            if(len(isInCourse)>0):
                if(department[0]=='Sistemas y Computación'):
                    capacitados[0]+=1
                elif(department[0]=='Ingenierías'):
                    capacitados[1]+=1
                elif(department[0]=='Ciencias Básicas'):
                    capacitados[2]+=1                    
                elif(department[0]=='Económico-Administrativo'):
                    capacitados[3]+=1
                elif(department[0]=='Ingeniería Industrial'):
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
        numOfCD = Course.objects.filter(typeCourse='Docente', dateStart__gte=dt.strptime('%s-01-01'%year, '%Y-%m-%d'), dateEnd__lte=dt.strptime('%s-12-31'%year, '%Y-%m-%d'))
        numOfAP = Course.objects.filter(typeCourse='Profesional', dateStart__gte=dt.strptime('%s-01-01'%year, '%Y-%m-%d'), dateEnd__lte=dt.strptime('%s-12-31'%year, '%Y-%m-%d'))
        totalCourses = [len(numOfCD), len(numOfAP)]
        return(concentrated(depName, depTeacherNum, depDocenteNum, depPercentDocent, depProfesionalNum, depPercentProfesional, depDocentProfesionalNum, depPercentDocentProf, capacitados, depPercentYesCoursed, noCapacitados, depPercentNoCoursed, totalCourses), 200)
