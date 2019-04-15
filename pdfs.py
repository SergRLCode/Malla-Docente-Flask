# -*- coding: utf-8 -*-

from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Image, PageTemplate, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from flask import make_response, send_file
from models import LetterheadMetaData
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import StringIO, BytesIO
from datetime import datetime

# Global variables to style
styles = getSampleStyleSheet()
styleH2 = styles['Heading2']
styleH2.alignment = TA_CENTER
styleN = styles['Normal']
styleN.fontSize = 8
styleN.leading = 10
styleN.alignment = TA_CENTER
_styleH1 = styles['Heading1']
_styleH1.fontSize = 11
_styleH1.leading = 15
_styleH1.alignment = TA_LEFT
_styles = getSampleStyleSheet()
_styleRN = _styles['Normal']
_styleRN.fontSize = 8
_styleRN.leading = 10
_styleRN.alignment = TA_RIGHT

def set_H2(text):
    return Paragraph(text.upper(), styleH2)
def set_N(text):
    return Paragraph(text, styleN)
def set_NU(text):
    return Paragraph(text.upper(), styleN)
def set_H1(text):
    return Paragraph(text, _styleH1)
def _set_N(text):
    return Paragraph(text, _styleRN)
def _set_NU(text):
    return Paragraph(text.upper(), _styleRN)
# Dict for metadata to landscapeLetterhead
metaData = {
    "nameDocument": "",
    "typeDocument": "",
    "version": "",
    "emitDate": ""
}

class PageNumCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    def draw_page_number(self, page_count):
        page = "%s de %s" % (self._pageNumber, page_count)
        self.setFont("Helvetica", 10)
        self.drawRightString(685, 514, page)

def getMetaData(pk):
    documentInfo = LetterheadMetaData.objects.get(pk = pk)
    global metaData
    for value in metaData:
        if(value=="emitDate"):
            metaData[value] = "{}/{}/{}".format(documentInfo[value].day, "0{}".format(documentInfo[value].month) if documentInfo[value].month < 10 else documentInfo[value].month, documentInfo[value].year)
        else:
            metaData[value] = documentInfo[value]

def landscapeLetterhead(design, doc):
    logoTec = Image('logotec.jpg', 77, 42) # 101, 56
    tableHeaderContent = [
        [logoTec, metaData["typeDocument"], 'Versión:', metaData["version"]],
        ['', Paragraph(metaData["nameDocument"], styleN), 'Fecha emisión:', metaData["emitDate"]],
        ['', '', 'Página:', '']
    ]
    tableHeader = Table(tableHeaderContent, style=[
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('ALIGN',(0, 0), (1, 2),'CENTER'),
        ('ALIGN',(3, 0), (3, 2),'CENTER'),
        ('GRID', (0,0), (3, 2), 0.5, colors.black),
        ('SPAN', (0,0), (0,2)),
        ('SPAN', (1,1), (1, 2))
    ], colWidths=(90, 370, 90, 72), rowHeights=14)
    tableHeader.wrapOn(design, 0, 0)
    tableHeader.drawOn(design, 85, 510)

def portraitLetterhead(design, doc):
    logoTec = Image('logotec.jpg', 77, 42) # 101, 56
    tableHeaderContent = [
        [logoTec, metaData["typeDocument"], 'Versión:', metaData["version"]],
        ['', Paragraph(metaData["nameDocument"], styleN), 'Fecha emisión:', metaData["emitDate"]],
        ['', '', 'Página:', '1 de 1']
    ]
    tableHeader = Table(tableHeaderContent, style=[
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('ALIGN',(0, 0), (1, 2),'CENTER'),
        ('ALIGN',(3, 0), (3, 2),'CENTER'),
        ('GRID', (0,0), (3, 2), 0.5, colors.black),
        ('SPAN', (0,0), (0,2)),
        ('SPAN', (1,1), (1, 2))
    ], colWidths=(90, 270, 90, 72), rowHeights=14)
    tableHeader.wrapOn(design, 0, 0)
    tableHeader.drawOn(design, 45, 710)

def returnPDF(story, name, size, top):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize = size, topMargin=top, bottomMargin=50)
    if(size==letter):
        doc.build(story, canvasmaker=PageNumCanvas, onFirstPage=portraitLetterhead, onLaterPages=portraitLetterhead)
    elif(size==landscape(letter)):
        doc.build(story, canvasmaker=PageNumCanvas, onFirstPage=landscapeLetterhead, onLaterPages=landscapeLetterhead)
    pdf_out = output.getvalue()
    output.close()
    response = make_response(pdf_out)
    response.headers['Content-Disposition'] = "attachment; filename={}.pdf".format(name)
    response.headers['Content-Type'] = 'application/pdf'
    return response
# --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <-- --> <--
def assistantList(teachers, courseTeacher, course):
    getMetaData("5cb0c0beab661b261edfea32")
    tableTitleList = [
        [set_H2("lista de asistencia")]
    ]
    presential = ""
    virtual = ""
    if  course["modality"] == "Presencial":                     
        presential = "X"
        virtual = " "
    else:
        virtual = "X"
        presential = " "
    months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    tableDataCourseList = [        
        ['', '', '', '', 'FOLIO:', course["serial"]],
        ['NOMBRE DEL EVENTO:', course["courseName"]],
        ['NOMBRE DEL INSTRUCTOR:', courseTeacher[0], 'DURACION:', "{} Hrs.".format(course["totalHours"]), 'HORARIO:', course["timetable"]],
        ['PERIODO: ', 'Del {} al {} de {} del {}'.format(course["dateStart"].day, course["dateEnd"].day, months[course["dateStart"].month-1], course["dateEnd"].year), "SEDE:", course["place"]],
        ['MODALIDAD: ', 'PRESENCIAL(' + presential + ')', 'VIRTUAL(' + virtual + ')']
    ]
    arrayDays = []
    for x in range(course["dateStart"].day, course["dateEnd"].day+1):
        arrayDays.append(x)
    tableDataTeacherList = [
        ['No.', 'NOMBRE DEL PARTICIPANTE', 'R.F.C.', 'DEPARTAMENTO ACADÉMICO', set_N('CUMPLIMIENTO DE ACTIVIDADES'), 'ASISTENCIA'],
        ['', '', '', '', '', 'L', 'M', 'M', 'J', 'V'],
        ['', '', '', '', '%', arrayDays[0], arrayDays[1], arrayDays[2], arrayDays[3], arrayDays[4]]
    ]
    for x in range(0, len(teachers)):
        tableDataTeacherList.append([
            str(x+1), teachers[x][0], teachers[x][1], teachers[x][2], '', '', '', '', '', ''
        ])
    tableSignsList = [
        [set_NU(courseTeacher[0]), set_N('ME. CLAUDIA CRUZ NAVARRO')],
        [set_N("NOMBRE Y FIRMA DEL INSTRUCTOR"), set_N("NOMBRE Y FIRMA DEL INSTRUCTOR")],
        [set_N("R.F.C.: {}".format(courseTeacher[1]))],
        [set_N('C.U.R.P.: campoSinAgregarxd')]
    ]
    tableTitle = Table(tableTitleList)
    tableDataCourse = Table(tableDataCourseList, style=[
            ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('SPAN', (3,3), (5,3)),
            ('LINEBELOW', (5,0), (6,0), 0.5, colors.black), #Folio
            ('LINEBELOW', (1,1), (6,1), 0.5, colors.black), #Nombre del evento
            ('LINEBELOW', (1,2), (1,2), 0.5, colors.black), #Nombre del instructor
            ('LINEBELOW', (1,3), (1,3), 0.5, colors.black), #Periodo
            ('LINEBELOW', (3,2), (3,2), 0.5, colors.black), #Duracion
            ('LINEBELOW', (5,2), (5,2), 0.5, colors.black), #Horario
            ('LINEBELOW', (3,3), (5,3), 0.5, colors.black)  #Sede
        ], rowHeights=12, colWidths=(130, 200, 60, 90, 50, 70)
    )
    tableDataTeacher = Table(tableDataTeacherList, style=[
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('ALIGN',(0, 0), (-1, 2),'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (5,0), (9, 0)),
        ('SPAN', (4,0), (4, 1)),
        ('SPAN', (3,0), (3, 2)),
        ('SPAN', (2,0), (2, 2)),
        ('SPAN', (1,0), (1, 2)),
        ('SPAN', (0,0), (0, 2)),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ], colWidths=(16, 170, 120, 170, 80, 16, 16, 16, 16, 16), rowHeights= 11)
    tableSigns = Table(tableSignsList, style=[
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
    ], colWidths=180, rowHeights=10)
    title = course["courseName"].replace(" ", "")
    story = []
    story.append(tableTitle)
    story.append(tableDataCourse)
    story.append(Spacer(1,inch/5))
    story.append(tableDataTeacher)
    story.append(Spacer(1,inch*3/4))
    story.append(KeepTogether(tableSigns))
    return returnPDF(story, title, landscape(letter), 105)
    
def coursesList(courses):
    getMetaData("5cb0b321ab661b1fea0178be")
    tableTitleList = [
        [set_H2("PERIODO JUNIO - AGOSTO 2018")]
    ]
    tableCoursesList = [
        ['No.', set_N('Nombre de los cursos'), 'Objetivo', set_N('Periodo de Realizacion'), 'Lugar', set_N('No. de horas x Curso'), 'Instructor', 'Dirigido a:', 'Observaciones']
    ]
    for x in range(0, len(courses)):
        tableCoursesList.append(
            [str(x+1), set_N(courses[x][0]), set_N(courses[x][1]), set_N(courses[x][2]), set_N(courses[x][3]), set_N(courses[x][4]), set_N(courses[x][5]), set_N(courses[x][6]), '']
        )
    tableSignsList = [
        ["Elaboró", "Aprobó"],
        ["", ""],
        ["Nombre y firma", "Nombre y firma"],
        ["Fecha:", "Fecha:"]
    ]
    tableTitle = Table(tableTitleList)
    tableCourses = Table(tableCoursesList, style=[
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('ALIGN',(0, 0), (-1, -1),'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ], colWidths=(30, 80, 80, 80, 60, 50, 60, 80, 80))
    tableSigns = Table(tableSignsList, style=[
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('ALIGN',(0, 0), (-1, -1),'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ], colWidths=200, rowHeights=(10, 20, 10, 10))
    story = []
    story.append(tableTitle)
    story.append(tableCourses)
    story.append(Spacer(1,inch/4))
    story.append(KeepTogether(tableSigns))
    return returnPDF(story, "ListaDeCursos", landscape(letter), 105)

def inscription():
    getMetaData("5cb0c16bab661b27708563a7")
    tableTitleList = [
        [set_H2("Cédula de Inscripción")]
    ]
    tableDateList = [
        [set_N("FECHA")],
        [set_N("DIA"), set_N('MES'), set_NU('año')],
        [datetime.now().day, "0{}".format(datetime.now().month) if datetime.now().month<10 else datetime.now().month, datetime.now().year]
    ]
    tablePersonalDataList = [
        [set_H1("1. DATOS PERSONALES")],
        [_set_N('Nombre: '), set_N(""), set_N(""), set_N("")],
        ["", set_N('Apellido Paterno'), set_N('Apellido Materno'), set_N('Nombre (s)')],
        [_set_NU('r.f.c.:'), set_N(''), _set_N('Telefono particular:'), set_N('')],
        [_set_N('Correo electronico:'), set_N('')]
    ]
    tableStudiesList = [
        [set_H1("2. ESTUDIOS")],
        [_set_N('Licenciatura'), "", _set_N('Maestría'), "", _set_N('Doctorado'), "", _set_N('Otro'), "", ""],
        [_set_N('Título en:'), set_N('')]
    ]
    tableLaboralDataList = [
        [set_H1("3. DATOS LABORALES")],
        [_set_N('Departamento académico:'), ""],
        [_set_N('Jefe Inmediato:'), ""],
        [_set_N('Puesto actual:'), ""],
        [_set_N('Horario:'), ""]
    ]
    tableCourseDataList = [
        [set_H1('4. DATOS DEL EVENTO')],
        [_set_N('Nombre del evento:'), ""],
        [_set_N('Nombre del instructor:'), ""],
        [_set_N('Modalidad:'), _set_N('Presencial'), "", _set_N('Virtual'), ""],
        [_set_N('Fecha de realización:'), ""],
        [_set_N('Horario:'), ""],
        [_set_N('Sede:'), ""]
    ]
    tableSignList = [
        [""],
        [set_N('FIRMA')]
    ]
    tableNoteList = [
        [set_N('Nota: Para considerar válida la inscripción es necesario que entregue al instructor o coordinador, debidamente requisitada y con letra legible.')]
    ]
    tableTitle = Table(tableTitleList)
    tableDate = Table(tableDateList, style=[
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),        
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('ALIGN',(0, 0), (-1, -1),'CENTER'),
        ('SPAN', (0, 0), (2, 0))
    ], colWidths=40, rowHeights=(10, 10, 15), hAlign='RIGHT')
    tablePersonalData = Table(tablePersonalDataList, style = [     
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, 0), 1, colors.black),
        ('ALIGN',(0, 0), (-1, -1),'LEFT'),
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('LINEBELOW', (1, 1), (-1, 1), 0.5, colors.black),
        ('LINEBELOW', (1, 3), (1, 3), 0.5, colors.black),
        ('LINEBELOW', (3, 3), (3, 3), 0.5, colors.black),
        ('SPAN', (0,0), (-1, 0))
    ], colWidths=(57, 145, 145, 145), rowHeights=(15, 12, 12, 12, 20))
    tableStudies = Table(tableStudiesList, style=[
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, 0), 1, colors.black),
        ('GRID', (1, 1), (1, 1), 0.5, colors.black),    # Licenciatura
        ('GRID', (3, 1), (3, 1), 0.5, colors.black),    # maestria
        ('GRID', (5, 1), (5, 1), 0.5, colors.black),    # doctorado
        ('GRID', (7, 1), (7, 1), 0.5, colors.black),    # otro
        ('GRID', (8, 1), (8, 1), 0.5, colors.black),    # otro field
        ('ALIGN',(0, 0), (-1, -1),'LEFT'),
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('SPAN', (1,2), (-1, 2)),
        ('SPAN', (0,0), (-1, 0))
    ], colWidths=(77, 22, 77, 22, 77, 22, 77, 22, 96), rowHeights=(15, 12, 12))
    tableLaboralData = Table(tableLaboralDataList, style=[
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, 0), 1, colors.black),
        ('SPAN', (0,0), (-1, 0)),     
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('LINEBELOW', (1, 1), (1, 1), 0.5, colors.black), #depa academico
        ('LINEBELOW', (1, 2), (1, 2), 0.5, colors.black),   # boss
        ('LINEBELOW', (1, 3), (1, 3), 0.5, colors.black),   # horario
    ], colWidths=(110, 382), rowHeights=(15, 12, 12, 12, 12))
    tableCourseData = Table(tableCourseDataList, style=[
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (1, 1), (4, 1), 0.5, colors.black), #event
        ('LINEBELOW', (1, 2), (4, 2), 0.5, colors.black), #teacher
        ('LINEBELOW', (1, 3), (4, 3), 0.5, colors.black), #modality
        ('LINEBELOW', (1, 4), (4, 4), 0.5, colors.black), #fecha inicio-end
        ('LINEBELOW', (1, 5), (4, 5), 0.5, colors.black), #horario
        ('BOX', (2, 3), (2, 3), 0.5, colors.black),
        ('BOX', (4, 3), (4, 3), 0.5, colors.black),
        ('SPAN', (0,0), (-1, 0)),     
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
    ], colWidths=(100, 126, 70, 126, 70), rowHeights=(15, 12, 12, 12, 12, 12, 12))
    tableSign = Table(tableSignList, style=[
        ('BOX', (0, 0), (-1, -1), 1, colors.black), 
        ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
        ('LINEBELOW', (0, 0), (0, 0), 0.5, colors.black)
    ], colWidths=120, rowHeights=(40, 12), hAlign='RIGHT')
    tableNote = Table(tableNoteList)
    story = []
    story.append(tableTitle)
    story.append(tableDate)
    story.append(Spacer(1, inch/4))
    story.append(tablePersonalData)
    story.append(Spacer(1, inch/4))
    story.append(tableStudies)
    story.append(Spacer(1, inch/4))
    story.append(tableLaboralData)
    story.append(Spacer(1, inch/4))
    story.append(tableCourseData)
    story.append(Spacer(1, inch/4))
    story.append(tableSign)
    story.append(Spacer(1, inch))
    story.append(tableNote)
    return returnPDF(story, "cedula", letter, 85)
