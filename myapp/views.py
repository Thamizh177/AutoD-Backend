from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from docker_workspace.engine2 import get_docker_client
from docker_workspace.container_manager import (list_containers,inspect_container,get_container_logs,start_container,stop_container,restart_container)
from docker_workspace.network_manager import *
from docker_workspace.resource_monitor import *
from docker_workspace.replica_manager import *
from .serializers import DockerContainerSerializer

class DockerConnectionView(APIView):

    def get(self, request):

        result = get_docker_client()

        if result["status"] == "connected":
            return Response(
                {
                    "status": "connected",
                    "message": result["message"],
                    "socket": result["socket"],
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": "error",
                "message": result["message"],
                "socket": result["socket"],
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class DockerContainerListView(APIView):

    def get(self, request):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get the connected Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Get containers from container_manager
        # --------------------------------------------------

        containers = list_containers(client)

        # --------------------------------------------------
        # Step 4: Serialize Docker container information
        # --------------------------------------------------

        serializer = DockerContainerSerializer(
            containers,
            many=True
        )

        # --------------------------------------------------
        # Step 5: Return response
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "docker_connection": engine_result["message"],
                "count": len(containers),
                "containers": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
        
        
class DockerContainerInspectView(APIView):

    def get(self, request, container_id):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Inspect container
        # --------------------------------------------------

        try:

            container_data = inspect_container(
                client,
                container_id
            )

        except Exception as e:

            return Response(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # --------------------------------------------------
        # Step 4: Return container information
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "container": container_data,
            },
            status=status.HTTP_200_OK,
        )
        
class DockerContainerLogsView(APIView):

    def get(self, request, container_id):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Get tail parameter
        # --------------------------------------------------

        tail = request.query_params.get("tail", 100)

        try:
            tail = int(tail)

        except ValueError:

            return Response(
                {
                    "status": "error",
                    "message": "tail must be an integer.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # Step 4: Get container logs
        # --------------------------------------------------

        try:

            logs = get_container_logs(
                client,
                container_id,
                tail=tail
            )

        except Exception as e:

            return Response(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # --------------------------------------------------
        # Step 5: Return logs
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "container_id": container_id,
                "tail": tail,
                "logs": logs,
            },
            status=status.HTTP_200_OK,
        )
        
class DockerContainerStartView(APIView):

    def post(self, request, container_id):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Start container
        # --------------------------------------------------

        try:

            start_container(
                client,
                container_id
            )

        except Exception as e:

            return Response(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # Step 4: Return success
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "message": "Container started successfully.",
                "container_id": container_id,
            },
            status=status.HTTP_200_OK,
        )
        
class DockerContainerStopView(APIView):

    def post(self, request, container_id):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Stop container
        # --------------------------------------------------

        try:

            stop_container(
                client,
                container_id
            )

        except Exception as e:

            return Response(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # Step 4: Return success
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "message": "Container stopped successfully.",
                "container_id": container_id,
            },
            status=status.HTTP_200_OK,
        )

class DockerContainerRestartView(APIView):

    def post(self, request, container_id):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Restart container
        # --------------------------------------------------

        try:

            restart_container(
                client,
                container_id
            )

        except Exception as e:

            return Response(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # Step 4: Return success
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "message": "Container restarted successfully.",
                "container_id": container_id,
            },
            status=status.HTTP_200_OK,
        )


class DockerNetworkListView(APIView):

    def get(self, request):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get connected Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Get Docker networks
        # --------------------------------------------------

        networks = list_networks(client)

        # --------------------------------------------------
        # Step 4: Return response
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "docker_connection": engine_result["message"],
                "count": len(networks),
                "networks": networks,
            },
            status=status.HTTP_200_OK,
        )
        

class DockerContainersByNetworkView(APIView):

    def get(self, request):

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":
            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        client = engine_result["client"]

        network_map = list_containers_by_network(client)

        return Response(
            {
                "status": "success",
                "networks": network_map,
            },
            status=status.HTTP_200_OK,
        )

class DockerContainerNetworkInspectView(APIView):

    def get(self, request, container_id):

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":
            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        client = engine_result["client"]

        network_info = inspect_container_networks(
            client,
            container_id
        )

        if not network_info:
            return Response(
                {
                    "status": "error",
                    "message": "Container not found or network information unavailable.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "status": "success",
                "network_info": network_info,
            },
            status=status.HTTP_200_OK,
        )


class DockerNetworkContainersView(APIView):

    def get(self, request, network_name):

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":
            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        client = engine_result["client"]

        containers = get_containers_on_network(
            client,
            network_name
        )

        containers_data = []

        for container in containers:

            containers_data.append(
                {
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                }
            )

        return Response(
            {
                "status": "success",
                "network": network_name,
                "count": len(containers_data),
                "containers": containers_data,
            },
            status=status.HTTP_200_OK,
        )
        
class DockerContainerNetworkIssuesView(APIView):

    def get(self, request, container_id):

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":
            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        client = engine_result["client"]

        network_info = inspect_container_networks(
            client,
            container_id
        )

        if not network_info:
            return Response(
                {
                    "status": "error",
                    "message": "Container not found or network information unavailable.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        issues = detect_network_issues(
            network_info
        )

        return Response(
            {
                "status": "success",
                "container_id": container_id,
                "issues": issues,
                "issue_count": len(issues),
            },
            status=status.HTTP_200_OK,
        )
        
class DockerContainerReconnectView(APIView):

    def post(self, request, container_id):

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":
            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        network_name = request.data.get("network_name")

        if not network_name:
            return Response(
                {
                    "status": "error",
                    "message": "network_name is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = engine_result["client"]

        try:

            reconnect_container(
                client,
                container_id,
                network_name
            )

        except ValueError as error:

            return Response(
                {
                    "status": "error",
                    "message": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as error:

            return Response(
                {
                    "status": "error",
                    "message": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "status": "success",
                "message": "Container reconnected successfully.",
                "container_id": container_id,
                "network": network_name,
            },
            status=status.HTTP_200_OK,
        )
        
class DockerNetworkEventsView(APIView):

    def get(self, request):

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":
            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        client = engine_result["client"]

        since = request.query_params.get("since")

        if since is not None:

            try:
                since = int(since)

            except ValueError:

                return Response(
                    {
                        "status": "error",
                        "message": "since must be an integer timestamp.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        events = get_network_events(
            client,
            since=since
        )

        return Response(
            {
                "status": "success",
                "count": len(events),
                "events": events,
            },
            status=status.HTTP_200_OK,
        )
        
class DockerNetworkSummaryView(APIView):

    def get(self, request):

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":
            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        client = engine_result["client"]

        summary = summarize_network_state(
            client
        )

        return Response(
            {
                "status": "success",
                "summary": summary,
            },
            status=status.HTTP_200_OK,
        )
        
class DockerContainerMetricsView(APIView):

    def get(self, request, container_id):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Create stats provider
        # --------------------------------------------------

        stats_provider = DockerStatsProvider(client)

        # --------------------------------------------------
        # Step 4: Get raw Docker statistics
        # --------------------------------------------------

        try:

            raw_stats = stats_provider.get_raw_stats(
                container_id
            )

        except Exception as error:

            return Response(
                {
                    "status": "error",
                    "message": str(error),
                    "container_id": container_id,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # --------------------------------------------------
        # Step 5: Parse Docker statistics
        # --------------------------------------------------

        try:

            metrics = MetricsParser.parse(
                container_id,
                raw_stats
            )

        except Exception as error:

            return Response(
                {
                    "status": "error",
                    "message": f"Failed to parse container metrics: {error}",
                    "container_id": container_id,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --------------------------------------------------
        # Step 6: Return live metrics
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "container_id": metrics.container_id,
                "metrics": {
                    "cpu_percent": metrics.cpu_percent,
                    "memory_usage": metrics.memory_usage,
                    "memory_limit": metrics.memory_limit,
                    "network_rx": metrics.network_rx,
                    "network_tx": metrics.network_tx,
                    "block_read": metrics.block_read,
                    "block_write": metrics.block_write,
                    "pids": metrics.pids,
                },
            },
            status=status.HTTP_200_OK,
        )
        
class DockerContainerThresholdView(APIView):

    def get(self, request, container_id):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --------------------------------------------------
        # Step 2: Get Docker client
        # --------------------------------------------------

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 3: Create stats provider
        # --------------------------------------------------

        stats_provider = DockerStatsProvider(client)

        # --------------------------------------------------
        # Step 4: Get raw statistics
        # --------------------------------------------------

        try:

            raw_stats = stats_provider.get_raw_stats(
                container_id
            )

        except Exception as error:

            return Response(
                {
                    "status": "error",
                    "message": str(error),
                    "container_id": container_id,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # --------------------------------------------------
        # Step 5: Parse metrics
        # --------------------------------------------------

        try:

            metrics = MetricsParser.parse(
                container_id,
                raw_stats
            )

        except Exception as error:

            return Response(
                {
                    "status": "error",
                    "message": f"Failed to parse metrics: {error}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --------------------------------------------------
        # Step 6: Evaluate thresholds
        # --------------------------------------------------

        evaluator = ThresholdEvaluator()

        level = evaluator.evaluate(metrics)

        # Calculate memory percentage for response

        if metrics.memory_limit > 0:

            memory_percent = (
                metrics.memory_usage /
                metrics.memory_limit
            ) * 100

        else:

            memory_percent = 0.0

        # --------------------------------------------------
        # Step 7: Return threshold information
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "container_id": container_id,
                "threshold": level.value,
                "metrics": {
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": memory_percent,
                },
                "limits": {
                    "cpu": {
                        "warn": evaluator.cpu_warn,
                        "critical": evaluator.cpu_critical,
                    },
                    "memory": {
                        "warn": evaluator.memory_warn,
                        "critical": evaluator.memory_critical,
                    },
                },
            },
            status=status.HTTP_200_OK,
        )
        
class DockerResourceSummaryView(APIView):

    def get(self, request):

        # --------------------------------------------------
        # Step 1: Check Docker connection
        # --------------------------------------------------

        engine_result = get_docker_client()

        if engine_result["status"] != "connected":

            return Response(
                {
                    "status": "error",
                    "message": engine_result["message"],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        client = engine_result["client"]

        # --------------------------------------------------
        # Step 2: Get all containers
        # --------------------------------------------------

        containers = client.containers.list(
            all=True
        )

        stats_provider = DockerStatsProvider(client)

        results = []

        # --------------------------------------------------
        # Step 3: Collect one snapshot
        # --------------------------------------------------

        for container in containers:

            try:

                raw_stats = stats_provider.get_raw_stats(
                    container.id
                )

                metrics = MetricsParser.parse(
                    container.id,
                    raw_stats
                )

                results.append(
                    {
                        "container_id": metrics.container_id,
                        "name": container.name,
                        "metrics": {
                            "cpu_percent": metrics.cpu_percent,
                            "memory_usage": metrics.memory_usage,
                            "memory_limit": metrics.memory_limit,
                            "network_rx": metrics.network_rx,
                            "network_tx": metrics.network_tx,
                            "block_read": metrics.block_read,
                            "block_write": metrics.block_write,
                            "pids": metrics.pids,
                        },
                    }
                )

            except Exception as error:

                results.append(
                    {
                        "container_id": container.id,
                        "name": container.name,
                        "error": str(error),
                    }
                )

        # --------------------------------------------------
        # Step 4: Return snapshot
        # --------------------------------------------------

        return Response(
            {
                "status": "success",
                "count": len(results),
                "containers": results,
            },
            status=status.HTTP_200_OK,
        )
        
class ReplicaListView(APIView):
    """
    Get all currently running replicas.
    """

    def get(self, request):
        try:
            manager = ReplicaManager()

            replicas = manager.get_replicas()

            return Response(
                {
                    "status": "success",
                    "replica_count": len(replicas),
                    "replicas": [
                        {
                            "name": container.name,
                            "id": container.short_id,
                            "status": container.status,
                        }
                        for container in replicas
                    ],
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {
                    "status": "error",
                    "message": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReplicaCountView(APIView):
    """
    Get the current number of running replicas.
    """

    def get(self, request):
        try:
            manager = ReplicaManager()

            count = manager.get_replica_count()

            return Response(
                {
                    "status": "success",
                    "replica_count": count,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {
                    "status": "error",
                    "message": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReplicaScaleUpView(APIView):
    """
    Create additional replicas.
    """

    def post(self, request):
        try:
            count = int(request.data.get("count", 1))

            if count <= 0:
                return Response(
                    {
                        "status": "error",
                        "message": "count must be greater than 0.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            manager = ReplicaManager()

            created = manager.scale_up(count)

            return Response(
                {
                    "status": "success",
                    "requested_count": count,
                    "created_count": len(created),
                    "created_replicas": [
                        {
                            "name": container.name,
                            "id": container.short_id,
                            "status": container.status,
                        }
                        for container in created
                    ],
                    "current_replica_count": (
                        manager.get_replica_count()
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except ValueError:
            return Response(
                {
                    "status": "error",
                    "message": "count must be an integer.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            return Response(
                {
                    "status": "error",
                    "message": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReplicaScaleDownView(APIView):
    """
    Remove additional replicas.
    """

    def post(self, request):
        try:
            count = int(request.data.get("count", 1))

            if count <= 0:
                return Response(
                    {
                        "status": "error",
                        "message": "count must be greater than 0.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            manager = ReplicaManager()

            removed = manager.scale_down(count)

            return Response(
                {
                    "status": "success",
                    "requested_count": count,
                    "removed_count": len(removed),
                    "removed_replicas": removed,
                    "current_replica_count": (
                        manager.get_replica_count()
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except ValueError:
            return Response(
                {
                    "status": "error",
                    "message": "count must be an integer.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            return Response(
                {
                    "status": "error",
                    "message": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReplicaScaleToView(APIView):
    """
    Scale the service to a requested target count.
    """

    def post(self, request):
        try:
            target_count = int(
                request.data.get("target_count")
            )

            if target_count < 0:
                return Response(
                    {
                        "status": "error",
                        "message": (
                            "target_count cannot be negative."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            manager = ReplicaManager()

            result = manager.scale_to(target_count)

            created_replicas = []
            removed_replicas = []

            for item in result:

                if hasattr(item, "name"):
                    created_replicas.append(
                        {
                            "name": item.name,
                            "id": item.short_id,
                            "status": item.status,
                        }
                    )

                else:
                    removed_replicas.append(item)

            return Response(
                {
                    "status": "success",
                    "requested_target": target_count,
                    "created_replicas": created_replicas,
                    "removed_replicas": removed_replicas,
                    "current_replica_count": (
                        manager.get_replica_count()
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except (TypeError, ValueError):
            return Response(
                {
                    "status": "error",
                    "message": (
                        "target_count must be an integer."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            return Response(
                {
                    "status": "error",
                    "message": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReplicaStatusView(APIView):
    """
    Get complete replica manager status.
    """

    def get(self, request):
        try:
            manager = ReplicaManager()

            result = manager.get_status()

            return Response(
                {
                    "status": "success",
                    "data": result,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {
                    "status": "error",
                    "message": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )