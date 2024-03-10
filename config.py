import os
import json
import logging
try:
    # Python 2.x
    from urllib import quote
except ImportError:
    # Python 3.x
    from urllib.parse import quote

logger = logging.getLogger(__name__)

def configure(app):
    # Let Redis decode responses from bytes to strings
    app.config['REDIS_DECODE_RESPONSES'] = True
    redis_password = None
    redis_dbname = None
    sentinel_addr = None
    sentinel_port = None
    redis_username = None
    if should_read_from_file_system():
        redis_username, redis_password = get_username_and_password_from_file_system()
        if not redis_password:
            logger.error("Couldn't read redis password from file system.")
            return

    # Handle Cloud Foundry with Sentinel
    if 'VCAP_SERVICES' in os.environ:
        services = json.loads(os.getenv('VCAP_SERVICES'))
        service = _get_service(services)
        creds = service['credentials']
        redis_password = creds['password']
        redis_dbname = quote(creds['name'], safe='')

        if 'sentinel_addrs' in creds:
            sentinel_addr = creds['sentinel_addrs']
            sentinel_port = creds['sentinel_port']
        else:
            sentinel_addr = os.getenv('REDIS_SENTINEL_HOST').split(",")  # example: 1.1.1.1,2.2.2.2
            sentinel_port = os.getenv('REDIS_SENTINEL_PORT')

    elif 'REDIS_SENTINEL_HOST' in os.environ:
        if not should_read_from_file_system():
            redis_password = os.getenv('REDIS_PASSWORD')
        redis_dbname = os.getenv('REDIS_DBNAME')
        sentinel_addr = os.getenv('REDIS_SENTINEL_HOST').split(",")
        sentinel_port = os.getenv('REDIS_SENTINEL_PORT')
    else:
        logger.warning("Couldn't configure redis")
        return

    if not os.getenv('NO_URL_QUOTING'):
        redis_password = quote(redis_password, safe='')
    sentinel_host = ",".join("%s:%s" % (addr, sentinel_port) for addr in sentinel_addr)
    app.config['REDIS_URL'] = 'redis+sentinel://:%s@%s/%s/0' % (redis_password, sentinel_host, redis_dbname)
    app.config['REDIS_PASSWORD'] = redis_password
    app.config['REDIS_USERNAME'] = redis_username
    app.config['SSL_ENABLED'] = get_boolean_val_from_env('REDIS_WEBCLI_SSL_ENABLED', False)
    app.config['SKIP_HOSTNAME_VALIDATION'] = get_boolean_val_from_env('REDIS_WEBCLI_SKIP_HOSTNAME_VALIDATION', False)
    app.config['USE_SENTINEL'] = get_boolean_val_from_env('USE_SENTINEL', True)


def should_read_from_file_system():
    return get_boolean_val_from_env('READ_FROM_FILE_SYSTEM', False)

def get_username_and_password_from_file_system():
    file_system_location = os.getenv('FILE_SYSTEM_LOCATION')
    redis_password = None
    redis_username = None
    if not file_system_location:
        logger.error("Missing FILE_SYSTEM_LOCATION from env variable.")
    else:
        try:
            with open(file_system_location) as json_file:
                credentials = json.load(json_file)
                redis_password = credentials['password']
                redis_username = credentials['username']

        except (FileNotFoundError, ValueError, KeyError):
            logger.error("Couldn't parse vault file %s", file_system_location)

    return redis_username, redis_password

def get_boolean_val_from_env(env_entry_name, default_value):
    val = os.getenv(env_entry_name)
    if val is None:
        return default_value

    if val.lower() == "true":
        return True

    if val.lower() == "false":
        return False

    logger.warning("ignoring value for: %s, should be either true/false", env_entry_name)
    return default_value

def _get_service(services):
    for service_name, instances in services.items():
        for instance in instances:
            if 'redis' in instance.get('tags', []):
                return instance
