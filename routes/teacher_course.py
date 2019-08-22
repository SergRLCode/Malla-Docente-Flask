from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Course, Teacher, Qualified
from datetime import datetime as dt
from flask import jsonify, request
from app import app

def periodOfTime(initDate, endDate):
    return 'Del {} al {} de {} del {}'.format(initDate.day, endDate.day, months[endDate.month-1], endDate.year) if initDate.month==endDate.month else 'Del {} de {} al {} de {} del {}'.format(initDate.day, months[initDate.month-1], endDate.day, months[endDate.month-1], endDate.year) if initDate.year==endDate.year else 'Del {} de {} del {} al {} de {} del {}'.format(initDate.day, months[initDate.month-1], initDate.year, endDate.day, months[endDate.month-1], endDate.year)

months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

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

@app.route('/coursesOf/<rfc>', methods=['GET'])
@jwt_required
def courses_of(rfc):
    if request.method == 'GET':
        data_courses = []
        courses = Course.objects.filter(teachersInCourse__contains=rfc).values_list('courseName', 'teacherRFC', 'dateStart')
        for val in courses:
            teacherData = Teacher.objects.filter(rfc=val[1]).values_list('name', 'fstSurname', 'sndSurname')
            qualifieds = Qualified.objects.filter(course=val[0]).values_list('approved', 'failed')
            try:
                status = 'Aprobado' if val[1] in qualifieds[0][0] else 'Reprobado' if val[1] in qualifieds[0][1] else 'Sin calificar'
            except:
                status = 'Sin calificar'
            data_courses.append(
                {
                    'course': val[0],
                    'teacher': '%s %s %s'%(teacherData[0][0], teacherData[0][1], teacherData[0][2]),
                    'qualified': status,
                    'year': val[2].year
                }
            )
        return jsonify({'courses': data_courses})

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
