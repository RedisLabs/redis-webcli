import threading
import time
import subprocess
try:
    # Python 2.x
    from urlparse import urlparse
    from urllib import quote
except ImportError:
    # Python 3.x
    from urllib.parse import urlparse, quote
from flask import Flask, render_template, request, jsonify, abort
from flask import current_app as capp
from flask_redis_sentinel import SentinelExtension
from flask_bootstrap import Bootstrap
from config import configure, should_read_from_file_system, get_username_and_password_from_file_system
import redis_sentinel_url
import redis

redis_sentinel = SentinelExtension()
sentinel = redis_sentinel.sentinel

app = Flask(__name__)

configure(app)
redis_sentinel.init_app(app)
Bootstrap(app)


class MemtierThread(threading.Thread):
    def __init__(self, master_ip, master_port, redis_password=None, argument_line="", **kwargs):
        try:
            # Python 3.x
            super().__init__(**kwargs)
        except TypeError:
            # Python 2.x
            super(MemtierThread, self).__init__(**kwargs)
        self._master_ip = master_ip
        self._master_port = master_port
        self._redis_password = redis_password
        self._argument_list = argument_line.split()
        self._output = ""
        self._return_code = None
        self._process = None

    def run(self):
        self._process = subprocess.Popen(["./memtier_benchmark", "-s", self._master_ip, "-p", self._master_port, "-a", self._redis_password] + self._argument_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, shell=False)
        while True:
            curr_output = self._process.stdout.readline().decode("utf-8")
            if "[RUN" in curr_output:
                temp_output = curr_output.split("[RUN")
                curr_output = "\n[RUN".join(temp_output)
            if curr_output == '':
                self._return_code = self._process.poll()
                if self._return_code != None:
                    return
            if curr_output:
                self._output = self._output + "\n" + curr_output.strip()

    def kill(self):
        if self._process:
            self._process.kill()
            self.join()
            self._process = None

    @property
    def output(self):
        return self._output

    @property
    def return_code(self):
        return self._return_code


@app.route('/execute', methods=['POST'])
def execute():
    success = False
    req = request.get_json()
    try:
        conn = get_conn_through_sentinel()
        response = conn.execute_command(*req['command'].split())
        success = True
    except redis.exceptions.ConnectionError:
        try:
            reload_username_password_from_file_system_if_needed()
            conn = get_conn_through_sentinel()
            response = conn.execute_command(*req['command'].split())
            success = True
        except Exception as err:
            response = 'Exception: %s' % str(err)
            app.logger.exception("execute err")
    except Exception as err:
        response = 'Exception: %s' % str(err)
        app.logger.exception("execute err")

    if isinstance(response, bytes):
        response = response.decode("utf-8")

    return jsonify({
        'response': response,
        'success': success
    })


def reload_username_password_from_file_system_if_needed(app):
    # It may be that the dynamic password was changed since the config was set
    if should_read_from_file_system():
        redis_username, redis_password = get_username_and_password_from_file_system(app)
        if not redis_password:
            raise Exception("Missing password from file system.")
        else:
            app.config["REDIS_PASSWORD"] = redis_password
            app.config["REDIS_USERNAME"] = redis_username


def get_conn_through_sentinel():
    # it would be nice to call sentinel.master_for
    # redis-py API here. But this does not work
    # when the bdb is configured with TLS
    # creating the connection directly instead

    master_info = get_master(app.config['REDIS_URL'])
    master_ip = str(master_info[0])
    master_port = str(master_info[1])

    connection_args = {
        "host": master_ip,
        "port": master_port,
        "password": app.config['REDIS_PASSWORD']
    }
    redis_username = app.config['REDIS_USERNAME']
    if redis_username:
        # if no user name is sent, Redis will use the default username.
        connection_args['username'] = redis_username

    if app.config['SSL_ENABLED']:
        ssl_cert_reqs = None if app.config['SKIP_HOSTNAME_VALIDATION'] else 'required'
        connection_args['ssl'] = True
        connection_args['ssl_cert_reqs'] = ssl_cert_reqs

    return redis.Redis(**connection_args)


def get_master(url):
    if not url.startswith('redis+sentinel://'):
        abort(406, "not supported")
    result = redis_sentinel_url.parse_sentinel_url(url)
    return sentinel.discover_master(result.default_client.service)


def update_memtier_message():
    while True:
        output = capp.memtier_process.stdout.readline()
        if output == '':
            return
        if output:
            capp.memtier_message = capp.memtier_message + "\n" + output.strip()

def is_memtier_running(check_alive=True):
    if not hasattr(capp, 'memtier_process') or not capp.memtier_process:
        return False
    if check_alive and not capp.memtier_process.isAlive():
        return False
    return True


@app.route('/memtier_benchmark/start', methods=['POST'])
def start_memtier_benchmark():
    if is_memtier_running():
        return jsonify({
            'response': "Memtier is running, can't run a new process",
            'success': False
        })
    req = request.get_json() or {}
    config = req.get("args", "")
    master_info = get_master(app.config['REDIS_URL'])
    master_ip = str(master_info[0])
    master_port = str(master_info[1])
    thread = MemtierThread(master_ip, master_port, app.config['REDIS_PASSWORD'], config)
    thread.start()
    capp.memtier_process = thread
    time.sleep(10)
    returncode = thread.return_code
    return jsonify({
        'response': capp.memtier_process.output,
        'success': not returncode
    })


@app.route('/memtier_benchmark/poll', methods=['GET'])
def poll_memtier_benchmark():
    if not is_memtier_running(False):
        return jsonify({
            'response': (True, "Memtier is not running, can't poll it"),
            'success': False
        })
    returncode = capp.memtier_process.return_code
    message = capp.memtier_process.output
    if returncode is not None:
        capp.memtier_process = None
    return jsonify({
        'response': (returncode != None, message),
        'success': not returncode
    })


@app.route('/memtier_benchmark/stop', methods=['POST'])
def stop_memtier_benchmark():
    if not is_memtier_running():
        return jsonify({
            'response': "Memtier is not running, can't kill it",
            'success': False
        })
    capp.memtier_process.kill()
    message = capp.memtier_process.output
    capp.memtier_process = None
    return jsonify({
        'response': message,
        'success': True
    })



@app.route('/masters', methods=['GET'])
def masters():
    success = False
    try:
        response = get_master(app.config['REDIS_URL'])
        success = True
    except Exception as err:
        response = 'Exception: %s' % str(err)
    return jsonify({
        'response': response,
        'success': success
    })


def get_conn_info(url):
    conn_info = []
    if url.startswith('redis://'):
        urlparts = urlparse(url)
        netloc = urlparts[1].partition(':')
        conn_info = [
            ('Address', netloc[0]),
            ('Port', (netloc[2] or '6379'))
        ]
    elif url.startswith('redis+sentinel://'):
        result = redis_sentinel_url.parse_sentinel_url(url)
        print(result.hosts)
        conn_info = [
            ('Sentinel Hosts', ','.join(['%s:%s' % (pair[0], pair[1])
                                         for pair in result.hosts])),
            ('Service', result.default_client.service)
        ]

    return conn_info


@app.route('/')
def index():
    return render_template('index.html', config=app.config,
                           conninfo=get_conn_info(app.config['REDIS_URL']))
