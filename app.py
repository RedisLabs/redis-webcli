import os
import json
try:
    # Python 2.x
    from urlparse import urlparse
    from urllib import quote
except ImportError:
    # Python 3.x
    from urllib.parse import urlparse, quote
from collections import OrderedDict
from flask import Flask, render_template, request, jsonify, abort
from flask_redis import FlaskRedis
from flask_redis_sentinel import SentinelExtension
from flask_bootstrap import Bootstrap
import redis_sentinel_url

redis_sentinel = SentinelExtension()
redis_db = redis_sentinel.default_connection
sentinel = redis_sentinel.sentinel

app = Flask(__name__)

# Let Redis decode responses from bytes to strings
app.config['REDIS_DECODE_RESPONSES'] = True

# Handle Cloud Foundry with Sentinel
if 'VCAP_SERVICES' in os.environ:
    services = json.loads(os.getenv('VCAP_SERVICES'))
    service = services.get('redislabs')[0]
    creds = service['credentials']
    redis_password = creds['password']
    if not os.getenv('NO_URL_QUOTING'):
        redis_password = quote(redis_password, safe='')

    if 'sentinel_addrs' in creds:
        sentinel_addr = creds['sentinel_addrs'][0]
        sentinel_port = creds['sentinel_port']
    else:
        sentinel_addr = os.getenv('REDIS_SENTINEL_HOST')  # example: 1.1.1.1,2.2.2.2
        sentinel_port = os.getenv('REDIS_SENTINEL_PORT')

    app.config['REDIS_URL'] = 'redis+sentinel://:%s@%s:%s/%s/0' % (
        redis_password,
        sentinel_addr,
        sentinel_port,
        quote(creds['name'], safe=''))
elif 'REDIS_SENTINEL_HOST' in os.environ:
    app.config['REDIS_URL'] = 'redis+sentinel://:%s@%s:%s/%s/0' % (
        os.getenv('REDIS_PASSWORD'),
        os.getenv('REDIS_SENTINEL_HOST'),
        os.getenv('REDIS_SENTINEL_PORT'),
        quote(os.getenv('REDIS_DBNAME'), safe=''))


redis_sentinel.init_app(app)
Bootstrap(app)


@app.route('/execute', methods=['POST'])
def execute():
    success = False
    req = request.get_json()
    try:
        response = redis_db.execute_command(*req['command'].split())
        success = True
    except Exception as err:
        response = 'Exception: %s' % str(err)
    return jsonify({
        'response': response,
        'success': success
    })


@app.route('/masters', methods=['GET'])
def masters():
    success = False
    url = app.config['REDIS_URL']
    if not url.startswith('redis+sentinel://'):
        abort(406, "not supported")
    result = redis_sentinel_url.parse_sentinel_url(url)
    try:
        response = sentinel.discover_master(result.default_client.service)
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
