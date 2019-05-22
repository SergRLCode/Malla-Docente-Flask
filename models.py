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
    courseName = db.StringField(required=True)
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
    typeCourse = db.StringField()
    # Assistant List Data
    serial = db.IntField()
    # Status
    state = db.StringField(choices=state_choice, default='Por empezar')

class Teacher(db.Document):
    userType_choice = (
        ('Docente', 'Docente'),
        ('Administrador', 'Administrador'),
        ('Comunicación', 'Comunicación'),
        ('Jefe de departamento', 'Jefe de departamento'),
    )
    departament_choice = (
        ("Ciencias Básicas", "Ciencias Básicas"),
        ("Desarrollo Académico", "Desarrollo Académico"),
        ("Económico-Administrativo", "Económico-Administrativo"),
        ("Ingenierías", "Ingenierías"),
        ("Ingeniería Industrial", "Ingeniería Industrial"),
        ("Sistemas y Computación", "Sistemas y Computación")
    )
    # Personal Data
    rfc = db.StringField(max_length=13, required=True, unique=True)
    name = db.StringField()
    fstSurname = db.StringField()
    sndSurname = db.StringField()
    numberPhone = db.StringField()
    email = db.StringField()
    # Academic Studies
    studyLevel = db.StringField()
    degree = db.StringField()
    speciality = db.StringField()
    # Laboral Data
    departament = db.StringField(choices=departament_choice)
    schedule = db.StringField()
    position = db.StringField()
    # Sesion Data
    userType = db.StringField(choices=userType_choice)
    pin = db.StringField()
    
class RequestCourse(db.Document):
    course = db.StringField()
    requests = db.ListField(db.StringField())

class Departament(db.Document):
    name = db.StringField()
    boss = db.StringField()

class LetterheadMetaData(db.Document):
    nameDocument = db.StringField()
    typeDocument = db.StringField()
    version = db.IntField()
    emitDate = db.DateTimeField()

class BlacklistJWT(db.Document):
    jwt = db.StringField(unique = True)
    identity = db.StringField()

class BlacklistRequest(db.Document):
    course = db.StringField()
    requests = db.ListField(db.StringField())

# python3, reserved word "dir", pa ver metodos

# Docente, Administrador, Comunicacion, Jefe de departamento

# mongodump --db Capacitacion               -- para exportar la DB
# mongorestore -d Capacitacion course.bson  -- para importar la DB
# mongorestore -d DB_name -c Collection_name db_backup.bson -- para importar una coleccion especifica de la DB