from django.urls import path

from .views import *


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
    
    # ======================================================
    # Network APIs
    # ======================================================

    path(
        "docker/networks/",
        DockerNetworkListView.as_view(),
        name="docker-networks",
    ),

    path(
        "docker/networks/containers/",
        DockerContainersByNetworkView.as_view(),
        name="docker-containers-by-network",
    ),

    path(
        "docker/containers/<str:container_id>/networks/",
        DockerContainerNetworkInspectView.as_view(),
        name="docker-container-networks",
    ),

    path(
        "docker/networks/<str:network_name>/containers/",
        DockerNetworkContainersView.as_view(),
        name="docker-network-containers",
    ),

    path(
        "docker/containers/<str:container_id>/network-issues/",
        DockerContainerNetworkIssuesView.as_view(),
        name="docker-container-network-issues",
    ),

    path(
        "docker/containers/<str:container_id>/reconnect/",
        DockerContainerReconnectView.as_view(),
        name="docker-container-reconnect",
    ),

    path(
        "docker/networks/events/",
        DockerNetworkEventsView.as_view(),
        name="docker-network-events",
    ),

    path(
        "docker/networks/summary/",
        DockerNetworkSummaryView.as_view(),
        name="docker-network-summary",
    ),
    
    # ======================================================
    # Resource monitor APIs
    # ======================================================
    
    path(
    "docker/containers/<str:container_id>/metrics/",
    DockerContainerMetricsView.as_view(),
    name="docker-container-metrics",
    ),

    path(
        "docker/containers/<str:container_id>/threshold/",
        DockerContainerThresholdView.as_view(),
        name="docker-container-threshold",
    ),

    path(
        "docker/resources/",
        DockerResourceSummaryView.as_view(),
        name="docker-resource-summary",
),
]