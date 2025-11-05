#!/usr/bin/env python3
import importlib.util
import os
import re
import subprocess
import sys
import time

import yaml
from BlackDynamite import _transaction

from motoko.bd_study import create_bd_studies
from motoko.task_manager import TaskManager

################################################################


def no_action(*args, **kwargs):
    pass


################################################################


class WorkflowVars:
    """Driver class for storing and accessing workflow variables,
    e.g., when performing an action upon finishing a task
    """

    def __init__(self, db_fname):
        from ZODB import DB, FileStorage

        self.db_fname = db_fname
        storage = FileStorage.FileStorage(self.db_fname)

        self.db = DB(storage)
        self.conn = self.db.open()
        self.root = self.conn.root()

    def __setattr__(self, name, value):
        if name not in ["db_fname", "db", "conn", "root"]:
            self.root[name] = value

        else:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        if name != "root" and name in self.root:
            return self.root[name]

        return object.__getattribute__(self, name)

    def __delattr__(self, name):
        if name in self.root:
            del self.root[name]
            return

        super().__delattr__(name)


################################################################################


class Workflow:
    """Workflow class representation

    It is:
    - a manager of blackdynamite sub-studies
    - a manager of event and firing actions
    """

    def __init__(self, filename):
        self.finished = False
        with open(filename) as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
            self.config_path = os.path.abspath(filename)
            self.directory = os.path.dirname(self.config_path)
        self.task_managers = dict(
            [(e, TaskManager(self, e)) for e in self.config["task_managers"]]
        )
        # possibility to name tasks with aliases
        self.aliases = {}
        if "aliases" in self.config:
            self.aliases = self.config["aliases"]
        self.orchestrator_script = self.config["orchestrator"]
        self.orchestrator_function = None
        self.actions = {}
        self._vars = None

    @property
    def vars(self):
        if self._vars is not None:
            return self._vars
        conf_dir = os.path.join(self.directory, ".wf")
        os.makedirs(conf_dir, exist_ok=True)

        db_fname = os.path.join(conf_dir, "wf.db")
        self._vars = WorkflowVars(db_fname)
        return self._vars

    def create(self, validated=None):
        import subprocess

        conf_dir = os.path.join(self.directory, ".wf")
        subprocess.run(f"rm -r {conf_dir}", shell=True)
        os.makedirs(conf_dir, exist_ok=True)
        create_bd_studies(self, validated=validated)

    def start_launcher_daemons(self, args=None):
        # Select job management scheme (SLURM, PBS, bash, etc)
        # Default is bash

        config = self.config
        if args is None:
            import argparse

            args = argparse.Namespace()
            args.bd_study = "all"
        config.update(vars(args))

        clargs = ""
        if "generator" in self.config:
            generator = self.config["generator"]
            clargs += "--generator " + generator
            k = generator.replace("Coat", "_options")
            if k in self.config:
                clargs += " --" + k + " "
                clargs += " ".join(self.config[k])

        for name, task_manager in self.task_managers.items():
            detach = True
            if args.bd_study != "all" and args.bd_study != name:
                continue

            if args.bd_study == name and args.do_not_detach:
                detach = False

            cmd = f"canYouDigIt launch_daemon --start {clargs}"
            if detach:
                cmd += " -d"
            subprocess.call(
                cmd,
                cwd=task_manager.study_dir,
                shell=True,
            )

    def __getattr__(self, name):
        if name in self.task_managers:
            return self.task_managers[name]

        if name in self.aliases:
            return self.__getattr__(self.aliases[name])

        return super().__getattr__(name)

    def get_orchestrator_function(self):
        if self.orchestrator_function is not None:
            return self.orchestrator_function

        fname, func_name = self.orchestrator_script.split(".")
        file_path = os.path.join(self.directory, fname + ".py")
        module_name = "orchestrator"
        print(f"loading: {file_path}")
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        self.orchestrator_function = getattr(module, func_name)
        return self.orchestrator_function

    def add_action(self, event_name, task="__all__", event=None, f=None):
        if (
            not self.is_run_filter(event)
            and not self.is_workflow_filter(event)
            and not isinstance(event, list)
            and not isinstance(event, str)
        ):
            raise RuntimeError(f"Unknown event description {event_name}")

        task_actions = self.actions.setdefault(task, {})
        task_actions[event_name] = event, f

    def add_error_handler(self, event="state = FAILED", f=no_action, **kwargs):
        def abort_orchestrator(*args, **kwargs):
            f(*args, **kwargs)
            print("ERROR: abort orchestrator")
            import sys

            sys.exit(-1)

        self.add_action("error_handler", event=event, f=abort_orchestrator, **kwargs)

    def is_run_filter(self, f):
        if not callable(f):
            return False

        import inspect

        sig = inspect.signature(f)
        params = sig.parameters
        names = [name for name, param in params.items()]
        if names == ["run", "job"]:
            return True
        return False

    def is_workflow_filter(self, f):
        if not callable(f):
            return False

        import inspect

        sig = inspect.signature(f)
        params = sig.parameters
        names = [name for name, param in params.items()]
        if names == ["workflow", "task_manager"]:
            return True
        return False

    @_transaction
    def fire_event(self, event_name, task_manager_name, f, trigger, params):
        if isinstance(trigger, bool):
            print(
                f"fire: event={event_name} "
                f"task_manager={task_manager_name} "
                f"val={trigger}"
            )
            import inspect

            if inspect.isgeneratorfunction(f):
                yield f(workflow=self, **params)
            else:
                f(workflow=self, **params)
        else:
            print(
                f"fire: event={event_name} "
                f"task_manager={task_manager_name} "
                f"val={[r.id for r, j in trigger]}"
            )
            import inspect

            if inspect.isgeneratorfunction(f):
                yield f(runs=trigger, workflow=self, **params)
            else:
                f(runs=trigger, workflow=self, **params)

    def check_events(self, **params):
        for task_manager_name in self.actions:
            for event_name, (event, f) in self.actions[task_manager_name].items():
                if task_manager_name == "__all__":
                    task_managers = self.task_managers.items()
                    # will iterate over all tasks
                else:
                    task_managers = [
                        (task_manager_name, getattr(self, task_manager_name))
                    ]

                for task_manager_name, task_manager in task_managers:
                    if self.is_run_filter(event):
                        for run, job in task_manager.select([]):
                            is_fired = event(run, job)
                            if is_fired:
                                break
                    elif self.is_workflow_filter(event):
                        is_fired = event(self, task_manager=task_manager)
                    elif isinstance(event, list):  # must be a blackdynamite request
                        is_fired = task_manager.select(event)
                    elif isinstance(event, str):  # must be a blackdynamite request
                        event = [e.strip() for e in re.split(r",|\band\b", event)]
                        is_fired = task_manager.select(event)
                    else:
                        raise RuntimeError(f"Unknown event description {event_name}")

                    if is_fired:
                        self.fire_event(
                            event_name, task_manager_name, f, is_fired, params
                        )

    def execute(self, **params):
        """Orchestrator function that executes an action upon finishing a task"""

        func = self.get_orchestrator_function()
        func(self, **params)

        if not hasattr(self.vars, "stage"):
            self.vars.stage = "init"

        while not self.finished:
            self.check_events(**params)
            time.sleep(2)

    def get_runs(self, run_list):
        requests = {}
        for uri in run_list:
            task_manager_name, _id = uri.split(".")
            _id = int(_id)
            tm = self.__getattr__(task_manager_name)
            requests.setdefault(task_manager_name, []).append(tm.connect().runs[_id])
        return requests
