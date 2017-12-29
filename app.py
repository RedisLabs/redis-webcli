from flask import Flask, render_template, request, jsonify
from flask_redis import FlaskRedis
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_envvar('APP_SETTINGS')

Bootstrap(app)

redis_db = FlaskRedis(app)

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
