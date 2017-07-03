#!/usr/bin/env python
# coding=utf-8
'Flask todo list api using flask-restful'
from flask import Flask, jsonify, abort, make_response, request
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)  # pylint: disable=C0103
api = Api(app)  # pylint: disable=C0103
tasks = []  # pylint: disable=C0103


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
        return jsonify({'tasks': tasks})

    @staticmethod
    def post():
        'Create a new task'
        if not request.get_json() or 'title' not in request.get_json():
            abort(400)

        if not tasks:
            new_id = 1
        else:
            new_id = tasks[-1]['id'] + 1
        task = {
            'id': new_id,
            'title': request.get_json()['title'],
            'description': request.get_json().get('description', ''),
            'done': False
        }

        tasks.append(task)
        return make_response(jsonify({'task': task}), 201)

    @staticmethod
    def delete():
        'Remote all the tasks'
        del tasks[:]
        return jsonify({'tasks': tasks})


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
    def get(task_id):
        'Return the task by id'
        task = [task for task in tasks if task['id'] == task_id]
        if not task:
            return make_response(jsonify({'error': 'Not found'}), 404)
        return jsonify({'task': task[0]})

    @staticmethod
    def put(task_id):
        'Update a task'
        task = [task for task in tasks if task['id'] == task_id]
        if not task:
            return make_response(jsonify({'error': 'Not found'}), 404)
        request_update = request.get_json()
        if request_update is None:
            return make_response(jsonify({'error': 'Not found'}), 404)

        if 'done' in request_update and \
                not isinstance(request_update['done'], bool):
            abort(404)

        task[0]['title'] = request_update.get('title', task[0]['title'])
        task[0]['description'] = request_update.get('description',
                                                    task[0]['description'])
        task[0]['done'] = request_update.get('done', task[0]['done'])

        return jsonify({'task': task[0]})

    @staticmethod
    def delete(task_id):
        'Delete a task'
        task = [task for task in tasks if task['id'] == task_id]
        if not task:
            abort(404)
        tasks.remove(tasks[0])
        return ('', 204)


api.add_resource(TaskListAPI, '/todo/api/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/tasks/<int:task_id>', endpoint='task')


if __name__ == '__main__':
    app.run(debug=True)
