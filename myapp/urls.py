from django.urls import path

from .views import (
    DockerConnectionView,
    DockerContainerListView,
    DockerContainerInspectView,
    DockerContainerLogsView,
    DockerContainerStartView,
    DockerContainerStopView,
    DockerContainerRestartView,
)


urlpatterns = [

    # ------------------------------------------------------
    # Docker connection
    # ------------------------------------------------------

    path(
        "docker/connect/",
        DockerConnectionView.as_view(),
        name="docker-connect",
    ),

    # ------------------------------------------------------
    # Containers
    # ------------------------------------------------------

    path(
        "docker/containers/",
        DockerContainerListView.as_view(),
        name="docker-containers",
    ),

    path(
        "docker/containers/<str:container_id>/inspect/",
        DockerContainerInspectView.as_view(),
        name="docker-container-inspect",
    ),

    path(
        "docker/containers/<str:container_id>/logs/",
        DockerContainerLogsView.as_view(),
        name="docker-container-logs",
    ),

    path(
        "docker/containers/<str:container_id>/start/",
        DockerContainerStartView.as_view(),
        name="docker-container-start",
    ),

    path(
        "docker/containers/<str:container_id>/stop/",
        DockerContainerStopView.as_view(),
        name="docker-container-stop",
    ),

    path(
        "docker/containers/<str:container_id>/restart/",
        DockerContainerRestartView.as_view(),
        name="docker-container-restart",
    ),
]