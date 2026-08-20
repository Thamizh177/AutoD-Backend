from django.db import models


class ReplicaGroup(models.Model):
    name = models.CharField(max_length=100)
    service_name = models.CharField(max_length=100)
    image = models.CharField(max_length=255)

    desired_replicas = models.PositiveIntegerField(default=1)
    min_replicas = models.PositiveIntegerField(default=1)
    max_replicas = models.PositiveIntegerField(default=5)
    current_replicas = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Container(models.Model):
    replica_group = models.ForeignKey(
        ReplicaGroup,
        on_delete=models.CASCADE,
        related_name="containers"
    )

    container_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=100)
    image = models.CharField(max_length=255)

    status = models.CharField(max_length=50)

    cpu_limit = models.FloatField(null=True, blank=True)
    memory_limit = models.BigIntegerField(null=True, blank=True)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ContainerMetric(models.Model):
    container = models.ForeignKey(
        Container,
        on_delete=models.CASCADE,
        related_name="metrics"
    )

    timestamp = models.DateTimeField()

    cpu_percent = models.FloatField()
    memory_usage = models.BigIntegerField()
    memory_percent = models.FloatField()

    network_rx = models.BigIntegerField(default=0)
    network_tx = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.container.name} - {self.timestamp}"


class ScalingPolicy(models.Model):

    METRIC_TYPES = [
        ("CPU", "CPU"),
        ("NGINX", "Nginx"),
        ("CONTAINER", "Container"),
    ]

    replica_group = models.ForeignKey(
        ReplicaGroup,
        on_delete=models.CASCADE,
        related_name="scaling_policies"
    )

    name = models.CharField(max_length=100)

    metric_type = models.CharField(
        max_length=20,
        choices=METRIC_TYPES
    )

    threshold = models.FloatField()

    min_replicas = models.PositiveIntegerField(default=1)
    max_replicas = models.PositiveIntegerField(default=5)

    cooldown_period = models.PositiveIntegerField(
        default=60,
        help_text="Cooldown period in seconds"
    )

    enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ScalingEvent(models.Model):

    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("SKIPPED", "Skipped"),
    ]

    TRIGGER_TYPES = [
        ("CPU", "CPU"),
        ("NGINX", "Nginx"),
        ("CONTAINER", "Container"),
    ]

    replica_group = models.ForeignKey(
        ReplicaGroup,
        on_delete=models.CASCADE,
        related_name="scaling_events"
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_TYPES
    )

    reason = models.TextField()

    previous_replicas = models.PositiveIntegerField()
    new_replicas = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    def __str__(self):
        return f"{self.replica_group.name} - {self.trigger_type}"