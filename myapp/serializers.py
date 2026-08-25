from rest_framework import serializers

from .models import (
    ReplicaGroup,
    Container,
    ContainerMetric,
    ScalingPolicy,
    ScalingEvent,
)


class ReplicaGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplicaGroup
        fields = "__all__"


class ContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = "__all__"


class ContainerMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerMetric
        fields = "__all__"


class ScalingPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScalingPolicy
        fields = "__all__"


class ScalingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScalingEvent
        fields = "__all__"

class DockerContainerSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    image = serializers.CharField()
    status = serializers.CharField()
    health = serializers.CharField()
    created = serializers.CharField(allow_null=True)
    ports = serializers.JSONField()