from flask_mongoengine import MongoEngine
from app import db, app
import datetime
import jwt

class Course(db.Document):
    Online = 'Virtual'
    Presential = 'Presencial'
    modality_choice = (
        (Online, 'Virtual'),
        (Presential, 'Presencial'),
    )
    Finished = 'Terminado'
    OnCourse = 'Cursando'
    ToStart = 'Por empezar'
    state_choice = (
        (Finished, 'Terminado'),
        (OnCourse, 'Cursando'),
        (ToStart, 'Por empezar'),
    )
    # Inscription Data
    courseName = db.StringField(required=True)
    teacherName = db.StringField(required=True)
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
    # Assistant List Data
    serial = db.IntField()
    # Other
    state = db.StringField(choices=state_choice)

class Teacher(db.Document):
    teacher = 'Docente'
    admin = 'Administrador'
    communication = 'Comunicacion'
    departamentBoss = 'Jefe de departamento'
    userType_choice = (
        (teacher, 'Docente'),
        (admin, 'Administrador'),
        (communication, 'Comunicacion'),
        (departamentBoss, 'Jefe de departamento'),
    )
    # Personal Data
    rfc = db.StringField(max_length=13, required=True)
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
    departament = db.StringField()
    schedule = db.StringField()
    position = db.StringField()
    # Sesion Data
    userType = db.StringField(choices=userType_choice)
    pin = db.StringField()
    
class LetterheadMetaData(db.Document):
    version = db.IntField()
    emitDate = db.StringField()
    nameDocument = db.StringField()
    typeDocument = db.StringField()

# python3, reserved word "dir", pa ver metodos

# Docente, Administrador, Comunicacion, Jefe de departamento

# mongodump --db Capacitacion               -- para exportar la DB
# mongorestore -d Capacitacion course.bson  -- para importar la DB
# mongorestore -d DB_name -c Collection_name db_backup.bson -- para importar una coleccion especifica de la DB