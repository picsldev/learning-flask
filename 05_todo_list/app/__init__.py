#!/usr/bin/env python
# coding=utf-8
'Flask todo list api using flask-restful'
from datetime import timedelta
# from functools import wraps
# import jwt
from flask import Flask, jsonify, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal, abort
from flask_jwt_extended import JWTManager, jwt_required
from app.users import users, is_user, check_login
from app.tokens import blacklisted_tokens
from app.tasks import tasks, task_fields
from app.register_api import registerapi_bp
from app.logout_api import logoutapi_bp
from app.login_api import loginapi_bp
from app.status_api import statusapi_bp


app = Flask(__name__)  # pylint: disable=C0103

api = Api(app)  # pylint: disable=C0103
app.config['SECRET_KEY'] = "secret_key"
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=3)
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']
app.config['JWT_IDENTITY_CLAIM'] = 'sub'
jwt = JWTManager(app)  # pylint: disable=C0103


@jwt.expired_token_loader
def my_expired_token_callback():
    'Loader function used when an expired token accesses a protected endpoint'
    return make_response(
        jsonify(
            {'message': 'Signature expired. Please log in again.'}), 401)


@jwt.revoked_token_loader
def my_revoked_token_callback():
    'Loader function used when a revoked token accesses a protected endpoint'
    return make_response(jsonify({'message': 'Blacklisted tokens.'}), 401)


@jwt.invalid_token_loader
def my_invalid_token_callback(error):  # pylint: disable=W0613
    'Loader function used when an invalid token accesses a protected endpoint'
    return make_response(
        jsonify({'message': 'Invalid token. Please log in again.'}), 401)


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    'Loader function to check when a token is blacklisted'
    jti = decrypted_token['jti']
    return jti in blacklisted_tokens


class TaskListAPI(Resource):
    'Task List Api'

    def __init__(self):
        'Init'
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                   help='No task title provided',
                                   location='json')
        self.reqparse.add_argument('description', type=str, default="",
                                   location='json')
        super(TaskListAPI, self).__init__()

    @staticmethod
    def get():
        'Return the list of tasks'
        return {'tasks': [marshal(task, task_fields) for task in tasks]}

    @jwt_required
    def post(self):
        'Create a new task'
        args = self.reqparse.parse_args()
        if not tasks:
            new_id = 1
        else:
            new_id = tasks[-1]['id'] + 1
        task = {
            'id': new_id,
            'title': args['title'],
            'description': args['description'],
            'done': False
        }
        tasks.append(task)
        return {'task': marshal(task, task_fields)}, 201

    @staticmethod
    def delete():
        'Remote all the tasks'
        del tasks[:]
        return {'tasks': marshal(tasks, task_fields)}


class TaskAPI(Resource):
    'Task Api'

    def __init__(self):
        'Init'
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super(TaskAPI, self).__init__()

    @staticmethod
    def get(id):  # pylint: disable=C0103,W0622
        'Return the task by id'
        return {'task': marshal(TaskAPI.find_task(id), task_fields)}

    @jwt_required
    def put(self, id):  # pylint: disable=C0103,W0622
        'Update a task'
        task = TaskAPI.find_task(id)
        args = self.reqparse.parse_args()
        for key, value in args.items():
            if value is not None:
                task[key] = value
        return {'task': marshal(task, task_fields)}

    @staticmethod
    def delete(id):  # pylint: disable=C0103,W0622
        'Delete a task'
        tasks.remove(TaskAPI.find_task(id))
        return ('', 204)

    @staticmethod
    def find_task(id):  # pylint: disable=C0103,W0622
        'Return the task by id, if not exist, return 404 code'
        try:
            return [task for task in tasks if task['id'] == id][0]
        except IndexError:
            abort(404, message='Task {} not found'.format(id))


api.add_resource(TaskListAPI, '/todo/api/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/tasks/<int:id>', endpoint='task')
app.register_blueprint(loginapi_bp, url_prefix='/todo/api/auth')
app.register_blueprint(statusapi_bp, url_prefix='/todo/api/auth')
app.register_blueprint(logoutapi_bp, url_prefix='/todo/api/auth')
app.register_blueprint(registerapi_bp, url_prefix='/todo/api/auth')

if __name__ == '__main__':
    app.run(debug=True)