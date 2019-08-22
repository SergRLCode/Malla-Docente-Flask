from flask_jwt_extended import get_jwt_identity
from functools import wraps
from flask import jsonify

def requires_access_level(access_level):
    def decorator(f):
        def notAllowed():
            return jsonify({'message': 'NOT ALLOWED'})
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if get_jwt_identity()[1] in access_level:
                return f(*args, **kwargs)
            else:
                return notAllowed()
        return decorated_function
    return decorator
