from marshmallow_mongoengine import ModelSchema
from flask_marshmallow import Marshmallow
from models import Course, Teacher, LetterheadMetaData, Departament, BlacklistJWT
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

class DepartamentSchema(ModelSchema):
    class Meta:
        model = Departament

class BlacklistJWTSchema(ModelSchema):
    class Meta:
        model = BlacklistJWT

courseSchema = CourseSchema()
courseSchemas = CourseSchema(many=True)

teacherSchema = TeacherSchema()
teacherSchemas = TeacherSchema(many=True)

letterheadSchema = LetterheadSchema()

departamentSchema = DepartamentSchema()

blacklistJWTSchema = BlacklistJWTSchema()

# class CourseSchema(marsh.Schema):
#     class Meta:
#         fields = ('name', 'description', 'dateStart', 'dateEnd', 'totalDays', 'modality', 'state', 'serial')

# .pyc file extension: this file makes more easy the exportation of any module from another file

    # {
    # "workbench.iconTheme": "material-icon-theme",
    # "window.zoomLevel": 0,
    # "workbench.colorTheme": "Blueberry dark theme",
    # "python.jediEnabled": false,
    # "liveServer.settings.donotShowInfoMsg": true,
    # "javascript.updateImportsOnFileMove.enabled": "always",
    # "liveServer.settings.NoBrowser": true,
    # "liveServer.settings.CustomBrowser": "firefox",
    # "workbench.startupEditor": "newUntitledFile",
    # "editor.suggestSelection": "first",
    # "vsintellicode.modify.editor.suggestSelection": "automaticallyOverrodeDefaultValue",
    # "editor.fontFamily": "Fira Code",
    # "editor.fontLigatures": true
    # }