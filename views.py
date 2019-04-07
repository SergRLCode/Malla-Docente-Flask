from reportlab.pdfgen import canvas
from flask import jsonify, request, make_response
from models import Course, Teacher
from pdfs import *
from app import app
from marsh import *
import hashlib

# encripted = hashlib.sha256("valor en string").hexdigest()

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
        return jsonify({"message": "Curso guardado con exito."})

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
            studyLevel = data["studyLevel"],
            studyType = data["studyType"],
            degree = data["degree"],
            pin = data["pin"]
        ).save()
        return jsonify(data)

@app.route('/teacher/<id>', methods=['GET', 'PUT', 'DELETE'])
def teacher(id):
    pass

@app.route('/certificate_view/<id>', methods=['GET'])
def certificate_view(id):
    try:
        teacher = Teacher.objects.get(pk=id)
    except Teacher.DoesNotExist:
        return jsonify({"message": "Don't exists"})
    if (request.method == 'GET'):
        return certificate(teacher)

@app.route('/course/<course_id>/assistantList_view', methods=['GET'])
def assistantList_view(course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return jsonify({"message": "Curso inexistente"})
    all_teachers = Teacher.objects.all()
    teachers = []
    # print course["dateEnd"].day
    # print dir(course["dateEnd"])
    for teacher in all_teachers:
        teachers.append([
            teacher["name"] + ' ' + teacher["firstSurname"] + ' ' + teacher["secondSurname"],
            teacher["rfc"],
            teacher["studyType"]]
        )
    return assistantList(teachers, course)

@app.route('/courses/coursesList', methods=['GET'])
def coursesList_view():
    all_courses = Course.objects.all()
    courses = []
    for course in all_courses:
        courses.append(course)
    return coursesList(courses)

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

@app.errorhandler(404)
def page_not_found(error):
    error = {
        "errorType": "404",
        "message": "Pagina no encontrada"
    }
    return jsonify(error),404
