"""
network_manager.py

Handles Docker network inspection and network-related operations.

This module is responsible for:

    - Listing Docker networks
    - Finding containers attached to networks
    - Inspecting a container's network configuration
    - Detecting basic network issues
    - Reconnecting containers to bridge networks
    - Reading Docker network/container events
    - Providing a high-level network snapshot

The Docker connection itself is handled by core.engine.
This module receives a connected DockerClient and performs
network operations using that client.
"""

from typing import Dict, List, Optional

from docker.models.networks import Network
from docker.models.containers import Container

# from engine2 import get_docker_client


# =====================================================================
# NETWORK DISCOVERY
# =====================================================================

def list_networks(client) -> List[Dict]:
    """
    Return information about all Docker networks.

    We return structured dictionaries instead of JSON strings so that
    other parts of the autoscaling system can directly work with the
    information.

    Example:

        [
            {
                "id": "...",
                "name": "chicmix-backend",
                "driver": "bridge",
                "scope": "local",
                "internal": False,
                "attachable": False,
                "labels": {},
                "containers": {...}
            }
        ]
    """

    networks_data = []

    try:

        networks = client.networks.list()

        for network in networks:

            attrs = network.attrs

            networks_data.append({
                "id": network.short_id,
                "name": network.name,
                "driver": attrs.get("Driver"),
                "scope": attrs.get("Scope"),
                "internal": attrs.get("Internal"),
                "attachable": attrs.get("Attachable"),
                "enable_ipv6": attrs.get("EnableIPv6"),
                "ipam": attrs.get("IPAM"),
                "options": attrs.get("Options"),
                "labels": attrs.get("Labels") or {},
                "containers": attrs.get("Containers") or {},
            })

    except Exception as error:

        print(
            f"[NetworkManager] Failed to list networks: {error}"
        )

    return networks_data


# =====================================================================
# CONTAINERS BY NETWORK
# =====================================================================

def list_containers_by_network(client) -> Dict[str, List[Dict]]:
    """
    Group containers according to the Docker networks they belong to.

    Example:

        {
            "chicmix-backend": [
                {
                    "id": "...",
                    "name": "chicmix-backend",
                    "ip_address": "172.x.x.x",
                    "mac_address": "..."
                }
            ],

            "chicmix-frontend": [
                ...
            ]
        }

    This is useful for service discovery.
    """

    network_map = {}

    try:

        # Include stopped containers as well because this is
        # discovery/diagnostic information.
        containers = client.containers.list(
            all=True
        )

        for container in containers:

            networks = (
                container.attrs
                .get("NetworkSettings", {})
                .get("Networks", {})
            )

            # ---------------------------------------------------------
            # Container has no network
            # ---------------------------------------------------------

            if not networks:

                network_map.setdefault(
                    "none",
                    []
                ).append({
                    "id": container.short_id,
                    "name": container.name
                })

                continue

            # ---------------------------------------------------------
            # Container belongs to one or more networks
            # ---------------------------------------------------------

            for network_name, network_data in networks.items():

                network_map.setdefault(
                    network_name,
                    []
                ).append({
                    "id": container.short_id,
                    "name": container.name,
                    "ip_address": network_data.get(
                        "IPAddress"
                    ),
                    "mac_address": network_data.get(
                        "MacAddress"
                    )
                })

    except Exception as error:

        print(
            "[NetworkManager] Failed to group containers "
            f"by network: {error}"
        )

    return network_map


# =====================================================================
# CONTAINER NETWORK INSPECTION
# =====================================================================

def inspect_container_networks(
    client,
    container_id: str
) -> Dict:
    """
    Return complete network information for one container.

    This lets the autoscaler inspect which networks a container
    belongs to before attempting operations such as creating replicas.
    """

    try:

        container: Container = client.containers.get(
            container_id
        )

        network_settings = (
            container.attrs
            .get("NetworkSettings", {})
        )

        networks = network_settings.get(
            "Networks",
            {}
        )

        return {
            "container_id": container.short_id,

            "container_name": container.name,

            "hostname": (
                container.attrs
                .get("Config", {})
                .get("Hostname")
            ),

            "networks": networks,

            "raw": network_settings
        }

    except Exception as error:

        print(
            "[NetworkManager] Failed to inspect networks "
            f"for {container_id}: {error}"
        )

        return {}


# =====================================================================
# FIND CONTAINERS ON A SPECIFIC NETWORK
# =====================================================================

def get_containers_on_network(
    client,
    network_name: str
) -> List[Container]:
    """
    Return Docker container objects attached to a specific network.

    This is useful for the autoscaler when it needs to discover
    which containers communicate through a particular network.
    """

    containers = []

    try:

        all_containers = client.containers.list(
            all=True
        )

        for container in all_containers:

            networks = (
                container.attrs
                .get("NetworkSettings", {})
                .get("Networks", {})
            )

            if network_name in networks:

                containers.append(container)

    except Exception as error:

        print(
            f"[NetworkManager] Failed to find containers "
            f"on network '{network_name}': {error}"
        )

    return containers


# =====================================================================
# NETWORK ISSUE DETECTION
# =====================================================================

def detect_network_issues(
    container_network_info: Dict
) -> List[str]:
    """
    Detect potential network problems from container network data.

    This function diagnoses problems only.

    It does NOT automatically repair them.
    """

    issues = []

    networks = container_network_info.get(
        "networks",
        {}
    )

    # ---------------------------------------------------------------
    # No network
    # ---------------------------------------------------------------

    if not networks:

        issues.append(
            "Container has no network attached"
        )

        return issues

    # ---------------------------------------------------------------
    # Host network
    # ---------------------------------------------------------------

    if "host" in networks:

        issues.extend(
            analyze_host_network_container(
                container_network_info
            )
        )

        return issues

    # ---------------------------------------------------------------
    # None network
    # ---------------------------------------------------------------

    if "none" in networks:

        issues.append(
            "Container uses 'none' network: "
            "no external connectivity by design"
        )

        return issues

    # ---------------------------------------------------------------
    # Bridge network checks
    # ---------------------------------------------------------------

    for network_name, network_data in networks.items():

        if not network_data.get("IPAddress"):

            issues.append(
                f"Container missing IP address in "
                f"bridge network '{network_name}'"
            )

    return issues


# =====================================================================
# HOST NETWORK ANALYSIS
# =====================================================================

def analyze_host_network_container(
    container_network_info: Dict
) -> List[str]:
    """
    Analyze a container using host networking.

    Host networking cannot be repaired by reconnecting the
    container to a Docker bridge network.
    """

    alerts = []

    networks = container_network_info.get(
        "networks",
        {}
    )

    if "host" not in networks:
        return alerts

    alerts.append(
        "Container is using host network: "
        "no network isolation from host"
    )

    alerts.append(
        "Host network containers cannot be "
        "network-repaired by Docker"
    )

    alerts.append(
        "Check for port conflicts with other "
        "services on the host"
    )

    alerts.append(
        "Docker DNS is unavailable in host network mode"
    )

    alerts.append(
        "Security risk: container shares host "
        "network namespace"
    )

    return alerts


# =====================================================================
# RECONNECT CONTAINER
# =====================================================================

def reconnect_container(
    client,
    container_id: str,
    network_name: str
) -> None:
    """
    Reconnect a container to a Docker bridge network.

    This function deliberately refuses to reconnect containers
    to host/none networks.
    """

    if network_name in (
        "host",
        "none"
    ):

        raise ValueError(
            "Cannot reconnect container to "
            "host/none network"
        )

    container: Container = client.containers.get(
        container_id
    )

    network: Network = client.networks.get(
        network_name
    )

    # ---------------------------------------------------------------
    # Disconnect first.
    #
    # An exception is ignored because the container may not currently
    # be connected to the network.
    # ---------------------------------------------------------------

    try:

        network.disconnect(
            container
        )

    except Exception:

        pass

    # ---------------------------------------------------------------
    # Connect to the requested network.
    # ---------------------------------------------------------------

    network.connect(
        container
    )


# =====================================================================
# DOCKER NETWORK EVENTS
# =====================================================================

def get_network_events(
    client,
    since: Optional[int] = None
) -> List[Dict]:
    """
    Collect Docker events related to network/container connectivity.

    Events include:

        connect
        disconnect
        create
        destroy
    """

    filters = {
        "type": [
            "network",
            "container"
        ],

        "event": [
            "connect",
            "disconnect",
            "create",
            "destroy"
        ]
    }

    collected_events = []

    try:

        events = client.events(
            decode=True,
            since=since,
            filters=filters
        )

        for event in events:

            collected_events.append({
                "time": event.get("time"),
                "type": event.get("Type"),
                "action": event.get("Action"),
                "actor": event.get("Actor")
            })

            # Prevent an API call from running forever.
            if len(collected_events) >= 100:

                break

    except Exception as error:

        print(
            f"[NetworkManager] Failed to collect "
            f"network events: {error}"
        )

    return collected_events


# =====================================================================
# NETWORK STATE SUMMARY
# =====================================================================

def summarize_network_state(
    client
) -> Dict:
    """
    Return a high-level snapshot of the Docker networking state.

    The autoscaling system can use this information for discovery
    and diagnostics.
    """

    return {

        "networks": list_networks(
            client
        ),

        "containers_by_network": (
            list_containers_by_network(
                client
            )
        ),

        "recent_events": get_network_events(
            client
        )
    }


# =====================================================================
# OPTIONAL LOCAL TEST
# =====================================================================

# if __name__ == "__main__":

#     docker_engine = get_docker_client()

#     if docker_engine["status"] != "connected":

#         print(
#             "Error: Unable to connect to Docker Engine."
#         )

#     else:

#         client = docker_engine["client"]

#         print(
#             "\nDocker connected successfully."
#         )

#         print(
#             "\nDocker Networks:"
#         )

#         print(
#             list_networks(client)
#         )

#         print(
#             "\nContainers by Network:"
#         )

#         print(
#             list_containers_by_network(client)
#         )