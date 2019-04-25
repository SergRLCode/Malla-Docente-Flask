from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

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

stylesSmall = getSampleStyleSheet()
styleNS = stylesSmall['Normal']
styleNS.fontSize = 5.83
styleNS.leading = 7
styleNS.alignment = TA_CENTER

stylesCenterMoreSmall = getSampleStyleSheet()
styleCNMS = stylesCenterMoreSmall['Normal']
styleCNMS.fontSize = 8
styleCNMS.leading = 10
styleCNMS.alignment = TA_CENTER

stylesMoreSmall = getSampleStyleSheet()
styleNMS = stylesMoreSmall['Normal']
styleNMS.fontSize = 6
styleNMS.leading = 8

def set_H2(text):
    return Paragraph(text.upper(), styleH2)

def set_N(text):
    return Paragraph(text, styleN)

def set_NU(text):
    return Paragraph(text.upper(), styleN)

def set_H1(text):
    return Paragraph(text, _styleH1)

def set_RN(text):
    return Paragraph(text, _styleRN)

def set_RNU(text):
    return Paragraph(text.upper(), _styleRN)

def set_SN(text, color):
    return Paragraph('<font color={}>{}</font>'.format(color, text), styleNS)

def set_SNU(text, color):
    return Paragraph('<font color={}>{}</font>'.format(color, text).upper(), styleNS)

def set_CNMS(text, color):
    return Paragraph('<font color={}>{}</font>'.format(color, text), styleCNMS)

def set_NMS(text, color):
    return Paragraph('<font color={}>{}</font>'.format(color, text), styleNMS)