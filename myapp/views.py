from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from docker_workspace.engine2 import get_docker_client
from docker_workspace.container_manager import (list_containers,inspect_container,get_container_logs,start_container,stop_container,restart_container)
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

