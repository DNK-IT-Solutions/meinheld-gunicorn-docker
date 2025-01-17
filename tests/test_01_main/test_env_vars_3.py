import os
import time

import docker
import requests
from docker.models.containers import Container

from ..utils import (
    CONTAINER_NAME,
    get_config,
    get_logs,
    get_response_text1,
    remove_previous_container,
)

client = docker.from_env()


def verify_container(container: Container, response_text: str) -> None:
    response = requests.get("http://127.0.0.1:8000")
    assert response.text == response_text
    config_data = get_config(container)
    assert config_data["host"] == "127.0.0.1"
    assert config_data["port"] == "9000"
    assert config_data["bind"] == "0.0.0.0:8080"
    logs = get_logs(container)
    assert "Checking for script in /app/prestart.sh" in logs
    assert "Running script /app/prestart.sh" in logs
    assert (
        "Running inside /app/prestart.sh, you could add migrations to this file" in logs
    )


def test_env_bind() -> None:
    name = os.getenv("NAME")
    docker_tag_startswith = os.getenv("DOCKER_TAG_STARTSWITH")
    image = f"{docker_tag_startswith}:{name}"
    response_text = get_response_text1()
    sleep_time = int(os.getenv("SLEEP_TIME", 1))
    remove_previous_container(client)
    container = client.containers.run(
        image,
        name=CONTAINER_NAME,
        environment={"BIND": "0.0.0.0:8080", "HOST": "127.0.0.1", "PORT": "9000"},
        ports={"8080": "8000"},
        detach=True,
    )
    time.sleep(sleep_time)
    verify_container(container, response_text)
    container.stop()
    # Test that everything works after restarting too
    container.start()
    time.sleep(sleep_time)
    verify_container(container, response_text)
    container.stop()
    container.remove()
