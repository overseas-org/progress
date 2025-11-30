from mysql_database import Database, DatabaseCreds

from logger import logger
from vars import db_creds

class Step:
    def __init__(self, step_index, name, description, id=0, done=False, status="pending"):
        self.step_id = id
        self.step_index = step_index
        self.name = name
        self.description = description
        self.status = status
        self._done = done

    def save_to_db(self, task_id):
        db = Database("Task", db_creds)
        db.add_object("step", { 
                    "name": self.name,
                    "description": self.description,
                    "status": self.status,
                    "done": str(self._done),
                    "task_id": task_id,
                    "step_index": self.step_index})
    
    def update_db(self):
        if self.step_id != 0:
            db = Database("Task", db_creds)
            db.update_object("step", self.step_id, {
                "description": self.description,
                "status": self.status,
                "done": str(self._done),
            })

    def start(self):
        self._done = False
        self.status = "in progress"
        self.update_db()

    def done(self, success=True):
        self._done = True
        if success:
            self.status = "success"
        else:
            self.status = "failed"
        self.update_db()

    def is_done(self):
        return self._done

    def get_status(self):
        return self.status


class Task:
    def __init__(self, name, steps, status="pending", id=0):
        self.id = id
        self.name = name
        self.status = status
        self._done = False
        if steps and isinstance(steps[0], Step):
            self.steps = steps
        else:
            self.steps = []
            for i, step in enumerate(steps):
                step_id = 0 if "id" not in step else step["id"]
                self.steps.append(Step(i, step["name"], step["description"], step_id, False if "done" not in step else step["done"] == "True",
                                  "pending" if "status" not in step else step["status"]))

    @classmethod
    def get(cls, task_id, as_dict=False):
        db = Database("Task", db_creds)
        task = db.get_object_by_id("task", task_id, as_dict=as_dict)
        steps = db.get_list_of_objects("step", {"task_id": task_id}, as_dict=True)
        if as_dict:
            task["steps"] = steps
            return task
        return Task(task.name, steps, task.status, task.id)

    def save_to_db(self):
        db = Database("Task", db_creds)
        task_id = db.add_object("task", {"name": self.name,
                               "status": self.status,
                               "done": str(self._done)})
        for step in self.steps:
            step.save_to_db(task_id)
        return task_id
    
    def update_db(self):
        if self.id != 0:
            db = Database("Task", db_creds)
            db.update_object("task", self.id, {
                               "status": self.status,
                               "done": str(self._done)})
        

    def start(self):
        self.status = "in progress"
        for step in self.steps:
            if step.step_index == 0:
                step.start()
                break
        self.update_db()

    def start_step(self, step_name):
        self.status = "in progress"
        self.done = False
        for step in self.steps:
            if step.name == step_name:
                step.start()
                break
        self.check_status()
        self.update_db()

    def check_status(self):
        done = True
        success = True
        pending = True
        for step in self.steps:
            if step.status != "pending":
                pending = False
            if not step.is_done():
                done = False
            if not step.get_status() == "success":
                success = False
        self._done = done
        if not done:
            if pending:
                self.status = "pending"
            else:
                self.status = "in progress"
        elif success:
            self.status = "success"
        else:
            self.status = "failed"
        self.update_db()
        return done

    def get_status(self):
        return self.status
    
    def finish_step(self, name, success=True):
        for step in self.steps:
            if step.name == name:
                step.done(success)
                self.check_status()
                return
        logger.error(f"no step named {name} found")
  
