"""
container_manager.py

This module handles all **container-level operations** using a provided DockerClient.
It assumes that the DockerClient is already validated and connected.

This module follows SOLID principles and is optimized for API usage.
"""

# ---------- Standard library imports ----------
from typing import List, Dict

# ---------- Docker SDK imports ----------
from docker.models.containers import Container
from engine2 import get_docker_client


# ============================================================
# LIST CONTAINERS
# ============================================================

def list_containers(client) -> List[Dict]:
    """
    Returns a lightweight list of all containers (running + stopped).

    This function is optimized for dashboards and APIs.
    It avoids expensive inspect calls and uses cached attributes only.
    """

    # Initialize the final list that will be returned
    containers_data: List[Dict] = []

    # Fetch all containers (including stopped ones)
    containers: List[Container] = client.containers.list(all=True)

    # Iterate over each container object
    for container in containers:

        # Safely extract container health status (may not exist)
        health_status = (
            container.attrs
            .get("State", {})
            .get("Health", {})
            .get("Status")
        )

        # Safely extract exposed ports mapping
        ports = (
            container.attrs
            .get("NetworkSettings", {})
            .get("Ports", {})
        )

        # Determine image name (fallback to image ID if no tag)
        image_name = (
            container.image.tags[0]
            if container.image.tags
            else container.image.short_id
        )

        # Append structured container info
        containers_data.append({
            "id": container.short_id,          # Short container ID
            "name": container.name,            # Container name
            "image": image_name,               # Image name or ID
            "status": container.status,        # running / exited / paused
            "health": health_status or "none", # healthy / unhealthy / none
            "created": container.attrs.get("Created"),
            "ports": ports
        })

    # Return final structured list
    return containers_data


# ============================================================
# INSPECT CONTAINER (HEAVY OPERATION)
# ============================================================

def inspect_container(client, container_id: str) -> Dict:
    """
    Returns detailed inspection data for a single container.

    WARNING:
    This is a heavy operation and should be used only when needed
    (e.g., user clicks on a container in UI).
    """

    # Fetch container object by ID or name
    container: Container = client.containers.get(container_id)

    # Extract full container metadata
    attrs: Dict = container.attrs

    # Return selected structured information
    return {
        "id": container.short_id,
        "name": container.name,
        "image": attrs.get("Config", {}).get("Image"),
        "restart_policy": attrs.get("HostConfig", {}).get("RestartPolicy"),
        "env_vars": attrs.get("Config", {}).get("Env", []),
        "volumes": attrs.get("Mounts", []),
        "networks": attrs.get("NetworkSettings", {}).get("Networks", {}),
        "raw": attrs  # Full metadata (useful for debugging)
    }
    


# ============================================================
# CONTAINER LOGS
# ============================================================

def get_container_logs(client, container_id: str, tail: int = 100) -> str:
    """
    Returns the last N lines of container logs.

    - Works for running and stopped containers
    - Combines stdout and stderr
    """

    # Fetch container object
    container: Container = client.containers.get(container_id)

    # Fetch logs safely
    logs: bytes = container.logs(
        tail=tail,
        stdout=True,
        stderr=True
    )

    # Decode logs into string and ignore decode errors
    return logs.decode("utf-8", errors="ignore")


# ============================================================
# PRIMITIVE CONTAINER ACTIONS
# ============================================================

def start_container(client, container_id: str) -> None:
    """
    Starts a stopped container.
    """

    # Fetch container
    container: Container = client.containers.get(container_id)

    # Start container
    container.start()


def stop_container(client, container_id: str) -> None:
    """
    Stops a running container.
    """

    # Fetch container
    container: Container = client.containers.get(container_id)

    # Stop container
    container.stop()


def restart_container(client, container_id: str) -> None:
    """
    Restarts a container.
    """

    # Fetch container
    container: Container = client.containers.get(container_id)

    # Restart container
    container.restart()


# engine_result = get_docker_client()
# if engine_result["status"] != "connected":
#     print("error connecting with docker")
# client = engine_result["client"]
# print("client details :",client)
# result = list_containers(client)
# print("/n")
# print(result)