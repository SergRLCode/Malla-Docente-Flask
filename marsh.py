from marshmallow_mongoengine import ModelSchema
from flask_marshmallow import Marshmallow
from models import Course, Teacher, LetterheadMetaData
from app import app

marsh = Marshmallow(app)


class CourseSchema(ModelSchema):
    class Meta:
        model = Course


class TeacherSchema(ModelSchema):
    class Meta:
        model = Teacher


class LetterheadSchema(ModelSchema):
    class Meta:
        model = LetterheadMetaData


courseSchema = CourseSchema()
courseSchemas = CourseSchema(many=True)

teacherSchema = TeacherSchema()
teacherSchemas = TeacherSchema(many=True)

letterheadSchema = LetterheadSchema()

# class CourseSchema(marsh.Schema):
#     class Meta:
#         fields = ('name', 'description', 'dateStart', 'dateEnd', 'totalDays', 'modality', 'state', 'serial')

# .pyc file extension: this file makes more easy the exportation of any module from another file
