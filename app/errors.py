from flask import jsonify

def badRequest(e):
    return jsonify(description="bad request", detail=e.description), 400

def unauthorized(e):
    return jsonify(description="authentication required"), 401