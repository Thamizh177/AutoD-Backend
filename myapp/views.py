from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from docker_workspace.engine2 import get_docker_client
from docker_workspace.container_manager import (list_containers,inspect_container,get_container_logs,start_container,stop_container,restart_container)
from docker_workspace.network_manager import *
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