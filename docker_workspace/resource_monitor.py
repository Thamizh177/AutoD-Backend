from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum
import time
from typing import List, Iterator, Tuple
from engine2 import get_docker_client
import json

@dataclass
class ContainerMetrics:
    container_id: str
    cpu_percent: float
    memory_usage: int        # bytes
    memory_limit: int        # bytes
    network_rx: int          # bytes
    network_tx: int          # bytes
    block_read: int          # bytes
    block_write: int         # bytes
    pids: int


class StatsProvider(ABC):

    @abstractmethod
    def get_raw_stats(self, container_id: str) -> Dict[str, Any]:
        pass
    
class DockerStatsProvider(StatsProvider):

    def __init__(self, docker_client):
        self._client = docker_client

    def get_raw_stats(self, container_id: str) -> dict:
        container = self._client.containers.get(container_id)
        return container.stats(stream=False)

class MetricsParser:

    @staticmethod
    def parse(container_id: str, stats: dict) -> ContainerMetrics:
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        
        
        # Determine CPU count safely (capacity, not usage)
        online_cpus = stats["cpu_stats"].get("online_cpus")

        if online_cpus and online_cpus > 0:
            cpu_count = online_cpus
        else:
            percpu_usage = stats["cpu_stats"]["cpu_usage"].get("percpu_usage")
            if percpu_usage:
                cpu_count = len(percpu_usage)
            else:
                cpu_count = 1  # final safe fallback

        # Calculate CPU percentage
        if system_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * cpu_count * 100
        else:
            cpu_percent = 0.0

        memory_usage = stats["memory_stats"]["usage"]
        memory_limit = stats["memory_stats"]["limit"]

        network = next(iter(stats["networks"].values()))
        rx_bytes = network["rx_bytes"]
        tx_bytes = network["tx_bytes"]

        blk_read, blk_write = 0, 0
        for entry in stats["blkio_stats"]["io_service_bytes_recursive"]:
            if entry["op"] == "Read":
                blk_read += entry["value"]
            elif entry["op"] == "Write":
                blk_write += entry["value"]

        pids = stats["pids_stats"]["current"]

        return ContainerMetrics(
            container_id=container_id,
            cpu_percent=cpu_percent,
            memory_usage=memory_usage,
            memory_limit=memory_limit,
            network_rx=rx_bytes,
            network_tx=tx_bytes,
            block_read=blk_read,
            block_write=blk_write,
            pids=pids,
        )

class ResourceMonitor:

    def __init__(self, stats_provider: StatsProvider):
        self._stats_provider = stats_provider

    def get_container_metrics(self, container_id: str) -> ContainerMetrics:
        raw_stats = self._stats_provider.get_raw_stats(container_id)
        return MetricsParser.parse(container_id, raw_stats)


class ThresholdLevel(Enum):
    OK = "ok"
    WARN = "warn"
    CRITICAL = "critical"
    

class ThresholdEvaluator:

    def __init__(
        self,
        cpu_warn: float = 70.0,
        cpu_critical: float = 90.0,
        memory_warn: float = 70.0,
        memory_critical: float = 90.0,
    ):
        self.cpu_warn = cpu_warn
        self.cpu_critical = cpu_critical
        self.memory_warn = memory_warn
        self.memory_critical = memory_critical

    def evaluate(self, metrics: ContainerMetrics) -> ThresholdLevel:
        cpu = metrics.cpu_percent
        memory_percent = (
            (metrics.memory_usage / metrics.memory_limit) * 100
            if metrics.memory_limit > 0 else 0
        )

        if cpu >= self.cpu_critical or memory_percent >= self.memory_critical:
            return ThresholdLevel.CRITICAL

        if cpu >= self.cpu_warn or memory_percent >= self.memory_warn:
            return ThresholdLevel.WARN

        return ThresholdLevel.OK



class ResourceMonitor:

    def __init__(
        self,
        stats_provider: StatsProvider,
        evaluator: ThresholdEvaluator,
        interval: int = 5,
    ):
        self._stats_provider = stats_provider
        self._evaluator = evaluator
        self._interval = interval
        self._running = False

    def monitor_containers(
        self, container_ids: List[str]
    ) -> Iterator[Tuple[ContainerMetrics, ThresholdLevel]]:

        self._running = True

        while self._running:
            for container_id in container_ids:
                try:
                    raw_stats = self._stats_provider.get_raw_stats(container_id)
                    metrics = MetricsParser.parse(container_id, raw_stats)
                    level = self._evaluator.evaluate(metrics)

                    yield metrics, level

                except Exception as exc:
                    # IMPORTANT: observe, don’t crash the system
                    print(f"[ResourceMonitor] Error reading {container_id}: {exc}")

            time.sleep(self._interval)

    def stop(self):
        self._running = False
        
engine_result = get_docker_client()
print(engine_result)
if engine_result["status"] != "connected":
    print("Error connecting to the docker")

client = engine_result["client"]
raw_stat = DockerStatsProvider(client)
container_id = "fb3e5386c8361f9a034b66efa9b8c9a85673306e1debe146bc420d90f57b0f34"
result = raw_stat.get_raw_stats(container_id)
print(result)
print(               )
print(json.dumps(result,indent=2))

metric = MetricsParser.parse(container_id, result)
print(metric)