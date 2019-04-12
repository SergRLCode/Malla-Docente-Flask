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

# Global variables to style
styles = getSampleStyleSheet()
styleN = styles['Normal']
styleN.fontSize = 8
styleN.leading = 10
styleN.alignment = TA_CENTER
styleH2 = styles['Heading2']
styleH2.alignment = TA_CENTER
# Dict for metadata to letterhead
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

def letterhead(design, doc):
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

def getMetaData(pk):
    documentInfo = LetterheadMetaData.objects.get(pk = pk)
    global metaData
    for value in metaData:
        if(value=="emitDate"):
            if documentInfo[value].month < 10:
                month = "0{}".format(documentInfo[value].month)
                metaData[value] = "{}/{}/{}".format(documentInfo[value].day, month, documentInfo[value].year)
            else:
                metaData[value] = "{}/{}/{}".format(documentInfo[value].day, documentInfo[value].month, documentInfo[value].year)
        else:
            metaData[value] = documentInfo[value]

def returnPDF(story, name):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize = landscape(letter), topMargin=105, bottomMargin=50)
    doc.build(story, canvasmaker=PageNumCanvas, onFirstPage=letterhead, onLaterPages=letterhead)
    pdf_out = output.getvalue()
    output.close()
    response = make_response(pdf_out)
    response.headers['Content-Disposition'] = "attachment; filename={}.pdf".format(name)
    response.headers['Content-Type'] = 'application/pdf'
    return response

def assistantList(teachers, course):
    getMetaData("5cb0c0beab661b261edfea32")
    tableTitleList = [
        [Paragraph("LISTA DE ASISTENCIA", styleH2)]
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
        ['NOMBRE DEL EVENTO:', course["courseName"], '', '', '', ''],
        ['NOMBRE DEL INSTRUCTOR:', course["teacherName"], 'DURACION:', str(course["totalHours"])+ " Hrs.", 'HORARIO:', course["timetable"]],
        ['PERIODO: ', 'Del ' + str(course["dateStart"].day) + ' al ' + str(course["dateEnd"].day) + ' de ' + months[course["dateStart"].month-1] + ' del ' + str(course["dateEnd"].year), 'SEDE: ', course["place"], '', ''],
        ['MODALIDAD: ', 'PRESENCIAL(' + presential + ')', 'VIRTUAL(' + virtual + ')', '', '', '']
    ]
    arrayDays = []
    for x in range(course["dateStart"].day, course["dateEnd"].day+1):
        arrayDays.append(x)
    tableDataTeacherList = [
        ['No.', 'NOMBRE DEL PARTICIPANTE', 'R.F.C.', 'DEPARTAMENTO ACADÉMICO', Paragraph('CUMPLIMIENTO DE ACTIVIDADES', styleN), 'ASISTENCIA', '', '', '', ''],
        ['', '', '', '', '', 'L', 'M', 'M', 'J', 'V'],
        ['', '', '', '', '%', arrayDays[0], arrayDays[1], arrayDays[2], arrayDays[3], arrayDays[4]]
    ]
    for x in range(0, len(teachers)):
        tableDataTeacherList.append([
            str(x+1), teachers[x][0], teachers[x][1], teachers[x][2], '', '', '', '', '', ''
        ])
    tableTitle = Table(tableTitleList)
    tableDataCourse = Table(tableDataCourseList, style=[
            ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('SPAN', (3,3), (5,3)),
            ('GRID', (5,1), (6,0), 0.5, colors.black),  #Folio
            ('GRID', (1,2), (5,1), 0.5, colors.black),  #Nombre del evento
            ('GRID', (1,3), (1,1), 0.5, colors.black),  #Nombre del instructor
            ('GRID', (1,4), (1,3), 0.5, colors.black),  #Periodo
            ('GRID', (3,3), (3,2), 0.5, colors.black),  #Duracion
            ('GRID', (5,3), (6,2), 0.5, colors.black),  #Horario
            ('GRID', (3,4), (5,3), 0.5, colors.black)   #Sede
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
    title = course["courseName"].replace(" ", "")
    story = []
    story.append(tableTitle)
    story.append(tableDataCourse)
    story.append(Spacer(1,inch/5))
    story.append(tableDataTeacher)
    return returnPDF(story, title)
    
def coursesList(courses):
    getMetaData("5cb0b321ab661b1fea0178be")
    tableTitleList = [
        [Paragraph("PERIODO JUNIO - AGOSTO 2018", styleH2)]
    ]
    tableCoursesList = [
        ['No.', Paragraph('Nombre de los cursos', styleN), 'Objetivo', Paragraph('Periodo de Realizacion', styleN), 'Lugar', Paragraph('No. de horas x Curso', styleN), 'Instructor', 'Dirigido a:', 'Observaciones']
    ]
    for x in range(0, len(courses)):
        tableCoursesList.append(
            [str(x+1), Paragraph(courses[x][0], styleN), Paragraph(courses[x][1], styleN), Paragraph(courses[x][2], styleN), Paragraph(courses[x][3], styleN), Paragraph(courses[x][4], styleN), Paragraph(courses[x][5], styleN), Paragraph(courses[x][6], styleN), '']
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
    return returnPDF(story, "ListaDeCursos")