import os
import json
import urllib
from flask import Flask, render_template, request, jsonify
from flask_redis import FlaskRedis
from flask_redis_sentinel import SentinelExtension
from flask_bootstrap import Bootstrap

redis_sentinel = SentinelExtension()
redis_db = redis_sentinel.default_connection

app = Flask(__name__)
redis_password = None

# Handle Cloud Foundry with Sentinel
if 'VCAP_SERVICES' in os.environ:
  services = json.loads(os.getenv('VCAP_SERVICES'))
  service = services.get('redislabs')[0]
  creds = service['credentials']
  redis_password = creds['password']
  app.config['REDIS_URL'] = 'redis+sentinel://:%s@%s:%s/%s/0' % (
    urllib.quote(creds['password'], safe=''),
    creds['sentinel_addrs'][0],
    creds['sentinel_port'],
    urllib.quote(creds['name'], safe=''))


redis_sentinel.init_app(app)
Bootstrap(app)

@app.route('/execute', methods=['POST'])
def execute():
    req = request.get_json()
    try:
        response = redis_db.execute_command(*req['command'].split())
    except Exception as err:
        response = 'Exception: %s' % err
    return jsonify({
        'response': response
    })

@app.route('/')
def inde():
    return render_template('index.html', config=app.config)
