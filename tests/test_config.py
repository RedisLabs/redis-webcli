import app
import os


def test_configure():
    os.environ["REDIS_SENTINEL_HOST"] = "10.128.0.226,10.129.3.16,10.130.0.135,10.130.0.13,10.129.0.135"
    os.environ["REDIS_SENTINEL_PORT"] = "8001"
    os.environ["REDIS_PASSWORD"] = "automation"
    os.environ["REDIS_DBNAME"] = "bdb-test"

    app.configure()
    assert app.app.config['REDIS_URL'] == "redis+sentinel://:automation@10.128.0.226:8001," \
                                          "10.129.3.16:8001,10.130.0.135:8001,10.130.0.13:8001,10.129.0.135:8001" \
                                          "/bdb-test/0"


def test_vcap_configure():
    os.environ = dict()
    os.environ["VCAP_SERVICES"] = """{
        "redislabs": [
            {
                "label": "redislabs",
                "provider": null,
                "plan": "medium-redis",
                "name": "redis-webcli-service-NRY6IA75",
                "tags": [
                    "redislabs",
                    "redis"
                ],
                "instance_name": "redis-webcli-service-NRY6IA75",
                "binding_name": null,
                "credentials": {
                    "host": "redis-1071.c1.sys.testpcfb7d42.qa.redislabs.com",
                    "sentinel_addrs": ["10.128.0.226","10.129.3.16","10.130.0.135","10.130.0.13","10.129.0.135"],
                    "sentinel_port": 8001,
                    "ip_list": [
                        "10.0.4.21"
                    ],
                    "name": "redis-webcli-db-NRY6IA75",
                    "password": "iGBnw-An_owEKhkoEMwdni7mnX_qHBSfyZc31AbbYlGqyE0x",
                    "port": 1071
                },
                "syslog_drain_url": null,
                "volume_mounts": []
            }
        ]
    }
    """
    os.environ["NO_URL_QUOTING"] = True
    app.configure()
    assert app.app.config['REDIS_URL'] == "redis+sentinel://:iGBnw-An_owEKhkoEMwdni7mnX_qHBSfyZc31AbbYlGqyE0x@10.128.0.226:8001," \
                                          "10.129.3.16:8001,10.130.0.135:8001,10.130.0.13:8001,10.129.0.135:8001" \
                                          "/redis-webcli-db-NRY6IA75/0"
