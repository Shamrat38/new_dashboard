from rest_framework import status

def standard_response(success, message, data=None, status_code=status.HTTP_200_OK):
    return {
        'success': success,
        'message': message,
        'data': data if data is not None else {},
    }, status_code
