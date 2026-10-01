"""
replica_manager.py

Responsible for managing application replicas.

The ReplicaManager does NOT decide when scaling should happen.

Its responsibility is only:

    - Discover current replicas
    - Scale up
    - Scale down
    - Maintain minimum and maximum replica limits

Docker operations are delegated to DockerAdapter.
"""

from docker_workspace.docker_adapter import *

class ReplicaManager:
    """
    Manages replicas of a Docker-based application.
    """

    def __init__(
        self,
        docker_adapter=None,
        service_prefix="chicmix-backend",
        min_replicas=1,
        max_replicas=5
    ):
        """
        Initialize the Replica Manager.

        Parameters
        ----------
        docker_adapter:
            DockerAdapter instance.

        service_prefix:
            Prefix used to identify backend containers.

        min_replicas:
            Minimum number of replicas allowed.

        max_replicas:
            Maximum number of replicas allowed.
        """

        # Use an existing adapter if one is supplied.
        # Otherwise create one.
        self.docker = (
            docker_adapter
            if docker_adapter is not None
            else DockerAdapter()
        )

        # Temporary prototype configuration.
        #
        # Later we can replace this with service discovery /
        # Docker labels so the autoscaler does not depend on
        # ChicMix-specific names.
        self.service_prefix = service_prefix

        # Scaling boundaries.
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas

    # ==================================================================
    # REPLICA DISCOVERY
    # ==================================================================

    def get_replicas(self):
        """
        Return the currently running backend replicas.

        For the current ChicMix prototype we use the existing
        prefix-based helper in DockerAdapter.
        """

        return self.docker.get_running_backend_containers(
            prefix=self.service_prefix
        )

    def get_replica_count(self):
        """
        Return the number of currently running replicas.
        """

        return len(self.get_replicas())

    # ==================================================================
    # REPLICA NAME
    # ==================================================================

    def _generate_replica_name(self):
        """
        Generate a unique name for the next replica.

        Example:

            chicmix-backend-1
            chicmix-backend-2
            chicmix-backend-3
        """

        existing_names = {
            container.name
            for container in self.get_replicas()
        }

        number = 1

        while True:

            candidate = (
                f"{self.service_prefix}-{number}"
            )

            if candidate not in existing_names:
                return candidate

            number += 1

    # ==================================================================
    # SCALE UP
    # ==================================================================

    def scale_up(self, count=1):
        """
        Create additional backend replicas.

        Parameters
        ----------
        count:
            Number of replicas to create.

        Returns
        -------
        list
            Successfully created containers.
        """

        current_count = self.get_replica_count()

        # Check maximum limit.
        if current_count >= self.max_replicas:

            print(
                "[ReplicaManager] "
                "Maximum replica limit reached."
            )

            return []

        # Don't create more replicas than the maximum.
        allowed = min(
            count,
            self.max_replicas - current_count
        )

        created_replicas = []

        for _ in range(allowed):

            replica_name = (
                self._generate_replica_name()
            )

            # ----------------------------------------------------------
            # Create replica using the existing backend container
            # as the source configuration.
            # ----------------------------------------------------------

            source = self.service_prefix

            container = (
                self.docker.create_replica_from_container(
                    source_container_name=source,
                    replica_name=replica_name
                )
            )

            if container is None:

                print(
                    f"[ReplicaManager] "
                    f"Failed to create {replica_name}"
                )

                continue

            # ----------------------------------------------------------
            # Wait until Docker reports that the replica is running.
            # ----------------------------------------------------------

            running = (
                self.docker.wait_until_running(
                    replica_name
                )
            )

            if running:

                created_replicas.append(
                    container
                )

                print(
                    f"[ReplicaManager] "
                    f"Replica {replica_name} is ready."
                )

            else:

                print(
                    f"[ReplicaManager] "
                    f"Replica {replica_name} failed to start."
                )

        return created_replicas

    # ==================================================================
    # SCALE DOWN
    # ==================================================================

    def scale_down(self, count=1):
        """
        Remove backend replicas.

        The original backend container is protected.

        Only additional replicas are removed.
        """

        replicas = self.get_replicas()

        # Never scale below minimum.
        removable_count = max(
            0,
            len(replicas) - self.min_replicas
        )

        if removable_count <= 0:

            print(
                "[ReplicaManager] "
                "Minimum replica limit reached."
            )

            return []

        count = min(
            count,
            removable_count
        )

        removed_replicas = []

        # --------------------------------------------------------------
        # Remove the newest replicas first.
        #
        # This is a simple strategy for our prototype.
        # --------------------------------------------------------------

        replicas = sorted(
            replicas,
            key=lambda container: container.name,
            reverse=True
        )

        for container in replicas[:count]:

            # Never remove the original backend.
            if container.name == self.service_prefix:
                continue

            success = (
                self.docker.remove_container(
                    container.name
                )
            )

            if success:

                removed_replicas.append(
                    container.name
                )

                print(
                    f"[ReplicaManager] "
                    f"Removed {container.name}"
                )

        return removed_replicas

    # ==================================================================
    # SCALE TO TARGET
    # ==================================================================

    def scale_to(self, target_count):
        """
        Scale the backend service to the requested number
        of replicas.

        Example:

            Current = 2
            Target  = 4

            Creates 2 replicas.

        Or:

            Current = 4
            Target  = 2

            Removes 2 replicas.
        """

        # Enforce limits.
        target_count = max(
            self.min_replicas,
            min(
                target_count,
                self.max_replicas
            )
        )

        current_count = self.get_replica_count()

        if target_count > current_count:

            difference = (
                target_count - current_count
            )

            return self.scale_up(
                difference
            )

        if target_count < current_count:

            difference = (
                current_count - target_count
            )

            return self.scale_down(
                difference
            )

        print(
            "[ReplicaManager] "
            "Already at requested replica count."
        )

        return []

    # ==================================================================
    # STATUS
    # ==================================================================

    def get_status(self):
        """
        Return a simple status snapshot.

        Useful later for the autoscaling engine/API.
        """

        replicas = self.get_replicas()

        return {
            "service": self.service_prefix,
            "replica_count": len(replicas),
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "replicas": [
                {
                    "name": container.name,
                    "status": container.status
                }
                for container in replicas
            ]
        }