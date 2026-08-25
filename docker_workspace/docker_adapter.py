"""
docker_adapter.py

Docker adapter for the autoscaling system.

This module provides a single interface for the autoscaler
to communicate with Docker.

The actual Docker connection is handled by the central
Docker connection manager in core.engine.

Existing container and network utility functions are reused
from:

    container_manager.py
    network_manager.py

The adapter is responsible for:
    - Docker connection
    - Container lifecycle operations
    - Container discovery
    - Container inspection
    - Network discovery
    - Replica creation/removal
    - Container statistics
    - Container health
"""

import time

from docker.errors import APIError, NotFound

# Central Docker connection manager
from engine2 import get_docker_client

# Existing container-management functions
from container_manager import (
    list_containers as manager_list_containers,
    inspect_container as manager_inspect_container,
)

# Existing network-management functions
from network_manager import (
    list_containers_by_network,
    inspect_container_networks,
)


class DockerAdapter:
    """
    Adapter responsible for communicating with Docker Engine.

    The adapter does NOT decide:

        "Should we scale?"

    It only performs Docker-related operations.

    The scaling decision will be handled by the
    scaling policy / autoscaling engine later.
    """

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def __init__(self):
        """
        Connect to Docker using the central Docker connection manager.

        We intentionally do NOT use:

            docker.from_env()

        here because core.engine already handles Docker discovery,
        socket detection and connection validation.
        """

        result = get_docker_client()

        if result["status"] != "connected":

            raise RuntimeError(
                f"Unable to connect to Docker: "
                f"{result['message']}"
            )

        # Store the connected Docker SDK client.
        self.client = result["client"]

        # Store the discovered Docker socket if available.
        self.socket = result.get("socket")

    # ==================================================================
    # DOCKER CONNECTION
    # ==================================================================

    def ping(self) -> bool:
        """
        Check whether Docker Engine is responding.

        Returns:
            True  -> Docker is reachable.
            False -> Docker is unavailable.
        """

        try:

            return self.client.ping()

        except Exception:

            return False

    # ==================================================================
    # CONTAINER DISCOVERY
    # ==================================================================

    def list_containers(self, all_containers=False):
        """
        Return container information.

        We reuse the existing list_containers() function from
        container_manager.py rather than duplicating the logic here.

        Args:
            all_containers:
                False -> running containers
                True  -> running + stopped containers

        Returns:
            List of dictionaries containing container information.
        """

        # The existing container manager currently always retrieves
        # all containers, so we use its implementation directly.
        #
        # For the autoscaler we normally care about running containers.
        containers = manager_list_containers(self.client)

        if all_containers:
            return containers

        # Filter the structured result to running containers.
        return [
            container
            for container in containers
            if container.get("status") == "running"
        ]

    def get_container(self, container_name):
        """
        Get the actual Docker Container object.

        This method is useful for operations such as:

            start
            stop
            restart
            remove
            stats
        """

        try:

            return self.client.containers.get(
                container_name
            )

        except NotFound:

            return None

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Unable to get container "
                f"{container_name}: {error}"
            )

            return None

    def container_exists(self, container_name) -> bool:
        """
        Check whether a container exists.
        """

        return (
            self.get_container(container_name)
            is not None
        )

    # ==================================================================
    # CONTAINER INSPECTION
    # ==================================================================

    def inspect_container(self, container_name):
        """
        Return detailed information about a container.

        Reuses the existing inspect_container() function
        from container_manager.py.
        """

        try:

            return manager_inspect_container(
                self.client,
                container_name
            )

        except NotFound:

            return None

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Unable to inspect "
                f"{container_name}: {error}"
            )

            return None

    def get_container_image(self, container_name):
        """
        Get the image used by a container.

        The information is obtained from the existing
        container inspection functionality.
        """

        information = self.inspect_container(
            container_name
        )

        if information is None:
            return None

        return information.get("image")

    def get_container_labels(self, container_name):
        """
        Get Docker labels belonging to a container.
        """

        information = self.inspect_container(
            container_name
        )

        if information is None:
            return {}

        raw = information.get("raw", {})

        return (
            raw
            .get("Config", {})
            .get("Labels", {})
            or {}
        )

    def get_container_status(self, container_name):
        """
        Return the current status of a container.

        Examples:

            running
            exited
            created
            paused
        """

        container = self.get_container(
            container_name
        )

        if container is None:
            return None

        container.reload()

        return container.status

    # ==================================================================
    # NETWORK DISCOVERY
    # ==================================================================

    def get_container_networks(self, container_name):
        """
        Return network information for a container.

        Reuses inspect_container_networks() from
        network_manager.py.
        """

        try:

            result = inspect_container_networks(
                self.client,
                container_name
            )

            return result.get(
                "networks",
                {}
            )

        except NotFound:

            return {}

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Unable to inspect networks for "
                f"{container_name}: {error}"
            )

            return {}

    def list_containers_by_network(self):
        """
        Group containers according to the Docker network
        they belong to.

        Reuses the existing network_manager implementation.
        """

        return list_containers_by_network(
            self.client
        )

    # ==================================================================
    # CONTAINER LIFECYCLE
    # ==================================================================

    def start_container(self, container_name) -> bool:
        """
        Start a stopped container.
        """

        container = self.get_container(
            container_name
        )

        if container is None:
            return False

        try:

            container.start()

            return True

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Failed to start "
                f"{container_name}: {error}"
            )

            return False

    def stop_container(self, container_name) -> bool:
        """
        Gracefully stop a running container.
        """

        container = self.get_container(
            container_name
        )

        if container is None:
            return False

        try:

            container.stop()

            return True

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Failed to stop "
                f"{container_name}: {error}"
            )

            return False

    def restart_container(self, container_name) -> bool:
        """
        Restart an existing container.
        """

        container = self.get_container(
            container_name
        )

        if container is None:
            return False

        try:

            container.restart()

            return True

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Failed to restart "
                f"{container_name}: {error}"
            )

            return False

    def remove_container(
        self,
        container_name,
        force=False
    ) -> bool:
        """
        Remove a container.

        Args:
            force:
                If True, remove even if the container is running.
        """

        container = self.get_container(
            container_name
        )

        if container is None:
            return False

        try:

            container.remove(
                force=force
            )

            return True

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Failed to remove "
                f"{container_name}: {error}"
            )

            return False

    # ==================================================================
    # GENERIC CONTAINER CREATION
    # ==================================================================

    def create_container(
        self,
        image,
        name,
        network=None,
        environment=None,
        command=None,
        ports=None,
        labels=None,
        restart_policy=None,
        detach=True
    ):
        """
        Create and start a generic Docker container.

        This method intentionally accepts configuration as arguments
        instead of hardcoding a particular application's image,
        network or container name.
        """

        try:

            container = self.client.containers.run(

                image=image,

                name=name,

                network=network,

                environment=environment,

                command=command,

                ports=ports,

                labels=labels,

                restart_policy=restart_policy,

                detach=detach
            )

            print(
                f"[DockerAdapter] "
                f"Created container: {name}"
            )

            return container

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Failed to create {name}: {error}"
            )

            return None

    # ==================================================================
    # REPLICA CREATION
    # ==================================================================

    def create_replica_from_container(
        self,
        source_container_name,
        replica_name
    ):
        """
        Create a new replica using the configuration of an
        existing container.

        This is important for our autoscaler.

        Instead of saying:

            image = "some-image"

        the autoscaler can inspect an existing workload and
        reproduce the relevant configuration.

        Configuration copied:

            - image
            - environment
            - command
            - labels
            - network
            - restart policy

        Host port mappings are intentionally NOT copied.

        Multiple replicas cannot all bind the same host port.
        Nginx will communicate with replicas through the Docker
        network instead.
        """

        source = self.get_container(
            source_container_name
        )

        if source is None:

            print(
                f"[DockerAdapter] "
                f"Source container "
                f"{source_container_name} not found."
            )

            return None

        try:

            # Refresh Docker metadata.
            source.reload()

            config = source.attrs.get(
                "Config",
                {}
            )

            host_config = source.attrs.get(
                "HostConfig",
                {}
            )

            network_settings = source.attrs.get(
                "NetworkSettings",
                {}
            )

            # ----------------------------------------------------------
            # IMAGE
            # ----------------------------------------------------------

            image = config.get(
                "Image"
            )

            # ----------------------------------------------------------
            # ENVIRONMENT
            # ----------------------------------------------------------

            environment = config.get(
                "Env",
                []
            )

            # ----------------------------------------------------------
            # COMMAND
            # ----------------------------------------------------------

            command = config.get(
                "Cmd"
            )

            # ----------------------------------------------------------
            # LABELS
            # ----------------------------------------------------------

            labels = (
                config.get("Labels")
                or {}
            )

            # ----------------------------------------------------------
            # NETWORK
            # ----------------------------------------------------------

            networks = network_settings.get(
                "Networks",
                {}
            )

            network = None

            if networks:

                # Use the first network attached to the
                # source container.
                network = next(
                    iter(networks.keys())
                )

            # ----------------------------------------------------------
            # RESTART POLICY
            # ----------------------------------------------------------

            restart_policy = host_config.get(
                "RestartPolicy"
            )

            if restart_policy:

                restart_policy = {
                    "Name": restart_policy.get(
                        "Name",
                        ""
                    ),
                    "MaximumRetryCount":
                        restart_policy.get(
                            "MaximumRetryCount",
                            0
                        )
                }

            # ----------------------------------------------------------
            # CREATE REPLICA
            # ----------------------------------------------------------

            return self.create_container(

                image=image,

                name=replica_name,

                network=network,

                environment=environment,

                command=command,

                labels=labels,

                restart_policy=restart_policy,

                # IMPORTANT:
                # No host ports are copied.
                ports=None,

                detach=True
            )

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Failed to create replica "
                f"{replica_name}: {error}"
            )

            return None

    # ==================================================================
    # CONTAINER READINESS
    # ==================================================================

    def wait_until_running(
        self,
        container_name,
        timeout=30
    ) -> bool:
        """
        Wait until a container reaches the running state.
        """

        start_time = time.time()

        while (
            time.time() - start_time
            < timeout
        ):

            container = self.get_container(
                container_name
            )

            if container is None:
                return False

            container.reload()

            if container.status == "running":

                print(
                    f"[DockerAdapter] "
                    f"{container_name} is running."
                )

                return True

            time.sleep(1)

        print(
            f"[DockerAdapter] "
            f"{container_name} did not become "
            f"running within {timeout} seconds."
        )

        return False

    # ==================================================================
    # HEALTH CHECK
    # ==================================================================

    def get_health_status(
        self,
        container_name
    ):
        """
        Return the Docker health status.

        Possible values:

            healthy
            unhealthy
            starting
            None
        """

        container = self.get_container(
            container_name
        )

        if container is None:
            return None

        container.reload()

        health = (
            container.attrs
            .get("State", {})
            .get("Health")
        )

        if health is None:
            return None

        return health.get(
            "Status"
        )

    def wait_until_healthy(
        self,
        container_name,
        timeout=60
    ) -> bool:
        """
        Wait until a container becomes healthy.

        If the container does not have a Docker health check,
        running status is considered sufficient for now.
        """

        start_time = time.time()

        while (
            time.time() - start_time
            < timeout
        ):

            container = self.get_container(
                container_name
            )

            if container is None:
                return False

            container.reload()

            if container.status != "running":

                time.sleep(1)

                continue

            health = self.get_health_status(
                container_name
            )

            # No health check configured.
            if health is None:

                return True

            if health == "healthy":

                return True

            if health == "unhealthy":

                return False

            time.sleep(1)

        return False

    # ==================================================================
    # CONTAINER STATISTICS
    # ==================================================================

    def get_container_stats(
        self,
        container_name
    ):
        """
        Return live statistics for a container.

        Docker provides:

            - CPU
            - Memory
            - Network
            - Block IO
            - PIDs
        """

        container = self.get_container(
            container_name
        )

        if container is None:
            return None

        try:

            return container.stats(
                stream=False
            )

        except APIError as error:

            print(
                f"[DockerAdapter] "
                f"Failed to get stats for "
                f"{container_name}: {error}"
            )

            return None

    # ==================================================================
    # RUNNING CONTAINERS
    # ==================================================================

    def get_running_containers(self):
        """
        Return all currently running Docker containers.

        This uses our existing container manager's discovery
        information.
        """

        containers = self.list_containers(
            all_containers=False
        )

        return containers

    def get_container_count(self):
        """
        Return the number of currently running containers.
        """

        return len(
            self.get_running_containers()
        )

    # ==================================================================
    # BACKEND HELPER
    # ==================================================================

    def get_running_backend_containers(
        self,
        prefix="chicmix-backend"
    ):
        """
        Return running backend containers.

        This prefix-based method is intentionally retained for
        the current ChicMix prototype.

        Later, we can replace this with Docker labels so the
        autoscaler becomes completely application-independent.
        """

        containers = self.client.containers.list()

        backend = []

        for container in containers:

            if container.name.startswith(
                prefix
            ):

                backend.append(
                    container
                )

        return backend