from flask import jsonify
from app import app

@app.errorhandler(404)
def page_not_found(error):
    error = {
        "errorType": "404",
        "message": "Pagina no encontrada"
        }
    return(jsonify(error), 404)
