from django.contrib import admin
from django.urls import path,include
from .views import ( DockerConnectionView,DockerConnectionView,DockerContainerListView,)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("docker/connect/",DockerConnectionView.as_view(),name="docker-connect",),
        path(
        "docker/connect/",
        DockerConnectionView.as_view(),
        name="docker-connect",
    ),

    path(
        "docker/containers/",
        DockerContainerListView.as_view(),
        name="docker-containers",
    ),
]
