# -*- coding: utf-8 -*-

from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Image, PageTemplate, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from flask import make_response, send_file
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import StringIO, BytesIO

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
        self.drawRightString(675, 514, page)

def membretado(design, doc):
    logoTec = Image('logotec.jpg', 77, 42) # 101, 56
    tableHeaderContent = [
        [logoTec, 'REGISTRO', 'Versión:', '0'],
        ['', 'LISTA DE ASISTENCIA', 'Fecha emisión:', '12/02/1990'],
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

def assistantList(teachers, course):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize = landscape(letter), topMargin=105)
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontSize = 8
    styleN.leading = 10
    styleN.alignment = TA_CENTER
    styleH2 = styles['Heading2']
    styleH2.alignment = TA_CENTER
    tableTitleList = [
        [Paragraph("LISTA DE ASISTENCIA", styleH2), ''],
        ['', '']
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
    i=0
    while i<len(teachers):
        tableDataTeacherList.append([
            str(i+1), teachers[i][0], teachers[i][1], teachers[i][2], '', '', '', '', '', ''
        ])
        i+=1    

    #Preguntar a la maestra Claudia o Alba sobre el espaciado entre la tabla de datos y las firmas

    tableTitle = Table(tableTitleList,
        style=[
            ('SPAN', (0, 0), (1, 1))
        ]
    )

    tableDataCourse = Table(tableDataCourseList, style=[
            ('VALIGN',(0, 0), (-1, -1),'MIDDLE'),
            # ('ALIGN',(0, 5), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('SPAN', (3,3), (5,3)),
            ('GRID', (5,1), (6,0), 0.5, colors.black),  #Folio
            ('GRID', (1,2), (5,1), 0.5, colors.black),  #Nombre del evento
            ('GRID', (1,3), (1,1), 0.5, colors.black),  #Nombre del instructor
            ('GRID', (1,4), (1,3), 0.5, colors.black),  #Periodo
            ('GRID', (3,3), (3,2), 0.5, colors.black),  #Duracion
            ('GRID', (5,3), (6,2), 0.5, colors.black),  #Horario
            ('GRID', (3,4), (5,3), 0.5, colors.black)  #Sede
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
    # Preguntar sobre los datos del curso a la maestra Claudia
    title = course["courseName"].replace(" ", "")
    story = []
    story.append(tableTitle)
    story.append(tableDataCourse)
    story.append(Spacer(1,inch/5))
    story.append(tableDataTeacher)
    # Agrega todo el contenido al documento 
    doc.build(story, canvasmaker=PageNumCanvas, onFirstPage=membretado, onLaterPages=membretado)
    pdf_out = output.getvalue()
    output.close()
    response = make_response(pdf_out)
    response.headers['Content-Disposition'] = "attachment; filename=" + title + ".pdf"
    response.headers['Content-Type'] = 'application/pdf'
    return response

def coursesList(courses):
    output = StringIO()
    doc = SimpleDocTemplate(output,pagesize = landscape(letter), topMargin=105)
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontSize = 8
    styleN.leading = 10
    styleN.alignment = TA_CENTER
    styleH2 = styles['Heading2']
    styleH2.alignment = TA_CENTER

    tableTitleList = [
        [Paragraph("PERIODO JUNIO - AGOSTO 2018", styleH2), ''],
        ['', '']
    ]

    tableTitle = Table(tableTitleList,
        style=[
            ('SPAN', (0, 0), (1, 1))
        ]
    )

    story = []
    story.append(tableTitle)
    doc.build(story, canvasmaker=PageNumCanvas, onFirstPage=membretado, onLaterPages=membretado)
    pdf_out = output.getvalue()
    output.close()
    response = make_response(pdf_out)
    response.headers['Content-Disposition'] = "attachment; filename=ListaDeCursos.pdf"
    response.headers['Content-Type'] = 'application/pdf'
    return response
