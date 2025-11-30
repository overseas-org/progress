from flask import Flask, request, Blueprint, jsonify
from flask_cors import CORS
from mysql_database import Database, DatabaseCreds
import os, logging


from progress.task import Task
from vars import db_creds

app = Flask(__name__)

CORS(app, supports_credentials=True)

bp = Blueprint('progress', __name__,
                        template_folder='templates')

@bp.route("/task", methods=["POST"])
def create_task():
	data = request.get_json()
	task = Task(data["name"], data["steps"])
	task_id = task.save_to_db()
	return jsonify({"task_id": task_id}), 200

@bp.route("/task", methods=["GET"])
def get_task():
	task_id = request.args["task_id"]
	task = Task.get(task_id, as_dict=True)
	return jsonify(task), 200

@bp.route("/start_task", methods=["POST"])
def start_task():
	task_id = request.args["task_id"]
	task = Task.get(task_id)
	task.start()
	return jsonify(f"task {task.name} started"), 200

@bp.route("/finish_step", methods=["POST"])
def finish_step():
	task_id = request.args["task_id"]
	data = request.get_json()
	task = Task.get(task_id)
	task.finish_step(data["step_name"], data["success"] == "true")
	return jsonify(f"tasks step {data["step_name"]} finished"), 200

@bp.route("/start_step", methods=["POST"])
def start_step():
	task_id = request.args["task_id"]
	data = request.get_json()
	task = Task.get(task_id)
	task.start_step(data["step_name"])
	return jsonify(f"tasks step {data["step_name"]} started"), 200

app.register_blueprint(bp, url_prefix="/api/progress") 

if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)