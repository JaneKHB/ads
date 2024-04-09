from flask import make_response, jsonify
from flask_restx import Resource, Namespace

ProcessNS = Namespace('Process API', description=f'')


@ProcessNS.route('/')
class ProcessAPIController(Resource):
    def get(self):
        response = make_response(jsonify({}), 200)
        response.headers['Content-type'] = 'application/json; charset=utf-8'
        return response