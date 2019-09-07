from flask_mongoengine import MongoEngine
from app import db, app
import datetime

class Course(db.Document):
    modality_choice = (
        ('Virtual', 'Virtual'),
        ('Presencial', 'Presencial'),
    )
    state_choice = (
        ('Terminado', 'Terminado'),
        ('Cursando', 'Cursando'),
        ('Por empezar', 'Por empezar'),
    )
    type_choice = (
        ('Docente', 'Docente'),
        ('Profesional', 'Profesional'),
    )
    # Inscription Data
    courseName = db.StringField(required=True, unique=True)
    teacherRFC = db.StringField(required=True)
    modality = db.StringField(choices=modality_choice)
    dateStart = db.DateTimeField()
    dateEnd = db.DateTimeField()  # 2019-04-08 13:21:08.456998 --> formato a ingresar para las fechas
    timetable = db.StringField()
    place = db.StringField()
    # Courses List Data
    teachersInCourse = db.ListField(db.StringField())
    description = db.StringField()
    totalHours = db.IntField()
    courseTo = db.StringField()
    typeCourse = db.StringField(choices=type_choice)
    # Assistant List Data
    serial = db.StringField()
    # Status
    state = db.StringField(choices=state_choice, default='Por empezar')

class CourseSerialToDocument(db.Document):
    course = db.StringField()
    rfc = db.StringField()
    serial = db.StringField()
    
class Teacher(db.Document):
    userType_choice = (
        ('Docente', 'Docente'),
        ('Administrador', 'Administrador'),
        ('Comunicación', 'Comunicación'),
        ('Jefe de departamento', 'Jefe de departamento'),
    )
    department_choice = (
        ('Sistemas y Computación', 'Sistemas y Computación'), 
        ('Ingenierías', 'Ingenierías'), 
        ('Ciencias Básicas', 'Ciencias Básicas'), 
        ('Económico-Administrativo', 'Económico-Administrativo'), 
        ('Ingeniería Industrial', 'Ingeniería Industrial'), 
        ('Desarrollo Académico', 'Desarrollo Académico'), 
        ('', '')
    )
    # Personal Data
    rfc = db.StringField(max_length=13, required=True, unique=True)
    curp = db.StringField(required=True)
    name = db.StringField()
    fstSurname = db.StringField()
    sndSurname = db.StringField()
    numberPhone = db.StringField()
    email = db.StringField()
    internal = db.BooleanField()
    # Academic Studies
    studyLevel = db.StringField()
    degree = db.StringField()
    speciality = db.StringField()
    # Laboral Data
    departament = db.StringField()
    schedule = db.StringField()
    position = db.StringField()
    # Sesion Data
    userType = db.StringField(choices=userType_choice)
    pin = db.StringField()

class RequestCourse(db.Document):
    course = db.StringField()
    requests = db.ListField(db.StringField())

class BlacklistRequest(db.Document):
    course = db.StringField()
    requests = db.ListField(db.StringField())

class Qualified(db.Document):
    course = db.StringField()
    approved = db.ListField(db.StringField())
    failed = db.ListField(db.StringField())

class LetterheadMetaData(db.Document):
    nameDocument = db.StringField()
    shortName = db.StringField()
    typeDocument = db.StringField()
    version = db.IntField()
    emitDate = db.DateTimeField()

class BlacklistJWT(db.Document):
    jwt = db.StringField(unique=True)
    identity = db.StringField()

# mongodump --db Capacitacion               -- para exportar la DB
# mongorestore -d Capacitacion course.bson  -- para importar la DB
# mongorestore -d DB_name -c Collection_name db_backup.bson -- para importar una coleccion especifica de la DB
