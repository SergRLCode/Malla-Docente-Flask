from models import Course, Teacher, RequestCourse, BlacklistRequest
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify, request
from app import app

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

