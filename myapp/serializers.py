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