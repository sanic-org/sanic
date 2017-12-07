import os
import sys
import subprocess
import signal
from threading import Thread
import requests
from time import sleep

sanic_project_content_one  = '''
from sanic import Sanic
from sanic import response

app = Sanic(__name__)


@app.route("/")
async def test(request):
    return response.json({"test": 1})


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, auto_reload=True)
'''

sanic_project_content_two  = '''
from sanic import Sanic
from sanic import response

app = Sanic(__name__)


@app.route("/")
async def test(request):
    return response.json({"test": 2})


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, auto_reload=True)
'''

process_id = None
def execute_cmd(command):
    process = subprocess.Popen(command, shell=True)
    global process_id
    process_id = process.pid
    process.communicate()


class TestAutoReloading:

    def test_reloading_after_change_file(self,capsys):
        if os.name != 'posix':
            return

        with capsys.disabled(): pass
        sanic_app_file_path = "simple_sanic_app.py"
        with open (sanic_app_file_path, "w") as _file:
            _file.write(sanic_project_content_one)

        cmd = ' '.join([sys.executable, sanic_app_file_path])
        thread = Thread(target=execute_cmd, args=(cmd,))
        thread.start()

        sleep(2) # wait for completing server start process
        response = requests.get("http://127.0.0.1:8000/").json()
        assert response == {"test": 1}

        with open (sanic_app_file_path, "w") as _file:
            _file.write(sanic_project_content_two)
        sleep(2) # wait for completing server start process
        response = requests.get("http://127.0.0.1:8000/").json()
        assert response == {"test": 2}

        thread.join(1)
        os.remove(sanic_app_file_path)

    def teardown_method(self, method):
            if process_id:
                root_proc_path = "/proc/%s/task/%s/children" % (process_id, process_id)
                if not os.path.isfile(root_proc_path):
                    return
                with open(root_proc_path) as children_list_file:
                    children_list_pid = children_list_file.read().split()
                for child_pid in children_list_pid:
                    os.kill(int(child_pid), signal.SIGTERM)
