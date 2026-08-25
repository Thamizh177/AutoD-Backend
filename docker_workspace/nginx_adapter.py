import time
import subprocess
from collections import deque
from base_adapter import BaseProxyAdapter


class NginxAdapter(BaseProxyAdapter):
    """
    Nginx proxy adapter.
    Collects request pressure metrics using:
    - stub_status
    - access logs (sliding window)
    """

    def __init__(
        self,
        status_url="http://127.0.0.1/nginx_status",
        access_log="/var/log/nginx/autoscale_access.log",
        window_seconds=10
    ):
        self.status_url = status_url
        self.access_log = access_log
        self.window_seconds = window_seconds

        # Stores (timestamp, status_code, latency_ms)
        self.request_window = deque()

    def collect_metrics(self) -> dict:
        """
        Collect and normalize proxy metrics.
        """
        self._read_recent_logs()

        rps = self._calculate_rps()
        avg_latency = self._calculate_avg_latency()
        error_rate = self._calculate_error_rate()
        active_connections = self._get_active_connections()

        return {
            "rps": rps,
            "avg_latency_ms": avg_latency,
            "error_rate": error_rate,
            "active_connections": active_connections
        }

    # ------------------------------------------------------------------
    # LOG PARSING
    # ------------------------------------------------------------------

    def _read_recent_logs(self):
        """
        Reads latest access log lines and updates sliding window.
        """
        try:
            output = subprocess.check_output(
                ["tail", "-n", "200", self.access_log],
                text=True
            )
        except Exception:
            return

        now = time.time()

        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) != 2:
                continue

            status = int(parts[0])
            latency_sec = float(parts[1])
            latency_ms = latency_sec * 1000

            self.request_window.append(
                (now, status, latency_ms)
            )

        # Drop old entries outside the window
        self._trim_window()

    def _trim_window(self):
        """
        Removes requests older than window_seconds.
        """
        cutoff = time.time() - self.window_seconds

        while self.request_window and self.request_window[0][0] < cutoff:
            self.request_window.popleft()

    # ------------------------------------------------------------------
    # METRIC CALCULATIONS
    # ------------------------------------------------------------------

    def _calculate_rps(self) -> float:
        """
        Requests per second over sliding window.
        """
        if not self.request_window:
            return 0.0

        return len(self.request_window) / self.window_seconds

    def _calculate_avg_latency(self) -> float:
        """
        Average request latency in milliseconds.
        """
        if not self.request_window:
            return 0.0

        total = sum(req[2] for req in self.request_window)
        return total / len(self.request_window)

    def _calculate_error_rate(self) -> float:
        """
        Percentage of 5xx responses.
        """
        if not self.request_window:
            return 0.0

        errors = sum(
            1 for req in self.request_window
            if 500 <= req[1] < 600
        )

        return errors / len(self.request_window)

    # ------------------------------------------------------------------
    # STUB STATUS
    # ------------------------------------------------------------------

    def _get_active_connections(self) -> int:
        """
        Reads active connections from nginx stub_status.
        """
        try:
            output = subprocess.check_output(
                ["curl", "-s", self.status_url],
                text=True
            )
        except Exception:
            return 0

        for line in output.splitlines():
            if "Active connections" in line:
                return int(line.split()[-1])

        return 0
