from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from docker_workspace.engine2 import get_docker_client
from docker_workspace.container_manager import list_containers
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