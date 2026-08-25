# core/engine.py
import os
import subprocess
import docker
import socket
from typing import Optional, Dict

COMMON_SOCKETS = [
    "/var/run/docker.sock",
    "/run/docker.sock",
    "~/.docker/desktop/docker.sock",      # Docker Desktop for Linux (example)
    "~/.docker/run/docker.sock",
    "~/.docker/docker.sock",
    "/mnt/wsl/shared-docker/docker.sock", # WSL-like
]

Home = os.path.expanduser("~/")

SAFE_SEARCH_DIRS = [
    "/home",
    "/run",
    "/var",
    "/tmp",
    Home,
]

def _is_unix_socket(path: str) -> bool:
    try:
        return os.path.exists(path) and stat_is_socket(path)
    except Exception:
        return False

def stat_is_socket(path: str) -> bool:
    try:
        mode = os.stat(path).st_mode #st_mode using this we can see file type and who has the permission (inode permission mode)
        # stat.S_ISSOCK is used, but to avoid importing stat repeatedly:
        import stat as _stat
        return _stat.S_ISSOCK(mode) # This line is used for checking the file type wether it is a socket file or not
    except Exception:
        return False

def _try_from_env_ping() -> Optional[docker.DockerClient]:
    """Try docker.from_env() and ping the daemon."""
    try:
        client = docker.from_env()
        client.ping()  # will raise if cannot contact
        return client
    except Exception:
        return None

def _docker_cli_can_talk() -> bool:
    """Try 'docker info' to check whether Docker CLI can talk to a daemon (no sudo)."""
    try:
        proc = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=6
        )
        return proc.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False

def _try_client_with_socket(path: str) -> Optional[docker.DockerClient]:
    """Attempt to create DockerClient with given unix socket and ping it."""
    try:
        base = path
        if not path.startswith("unix://"):
            base = f"unix://{path}"
        client = docker.DockerClient(base_url=base)
        client.ping()
        return client
    except Exception:
        return None

def _safe_search_socket(max_depth:int = 3) -> Optional[str]:
    """
    Walk safe directories shallowly to find docker.sock.
    - avoids permission noise by catching exceptions.
    - limits depth to avoid scanning root.
    """
    for top in SAFE_SEARCH_DIRS:
        top = os.path.expanduser(top)
        if not os.path.isdir(top):
            continue
        # simple BFS using os.walk but break when reaching a depth limit
        try:
            for root, dirs, files in os.walk(top, topdown=True):
                # compute depth relative to top
                rel = os.path.relpath(root, top)
                depth = 0 if rel == "." else rel.count(os.sep) + 1
                if depth > max_depth:
                    # prune deeper directories
                    dirs[:] = []
                    continue

                # check for 'docker.sock' file in this directory
                if "docker.sock" in files:
                    candidate = os.path.join(root, "docker.sock")
                    if os.path.exists(candidate):
                        return candidate
        except Exception:
            # skip directories we cannot access
            continue
    return None

def get_docker_client() -> Dict:
    """
    Tries multiple robust ways to get a connected docker client.
    Returns a dict with:
      - status: "connected" / "partial" / "error"
      - client: DockerClient (if connected)
      - socket: discovered socket path (if any)
      - message: helpful message
    """
    # 1) Try docker.from_env() (uses DOCKER_HOST, docker context etc)
    client = _try_from_env_ping()
    if client:
        return {"status": "connected", "client": client, "socket": None, "message": "Connected via docker.from_env() (environment/context)."}

    # 2) If docker CLI exists and can talk, prefer using from_env() (but we already tried)
    cli_ok = _docker_cli_can_talk()
    if cli_ok:
        # sometimes docker CLI has contexts/config that python sdk will pick up after this check,
        # try from_env again
        client = _try_from_env_ping()
        if client:
            return {"status": "connected", "client": client, "socket": None, "message": "Connected via docker CLI context (docker info succeeded)."}
        # else continue to socket search paths

    # 3) Check DOCKER_HOST env var
    docker_host = os.environ.get("DOCKER_HOST")
    if docker_host:
        # case: unix:///path/to/socket or tcp://host:port
        if docker_host.startswith("unix://"):
            path = docker_host.replace("unix://", "", 1)
            if os.path.exists(path):
                client = _try_client_with_socket(path)
                if client:
                    return {"status": "connected", "client": client, "socket": path, "message": f"Connected using DOCKER_HOST unix socket ({path})."}
            # else fallthrough
        else:
            # could be tcp - try docker.DockerClient with DOCKER_HOST directly
            try:
                client = docker.DockerClient(base_url=docker_host)
                client.ping()
                return {"status": "connected", "client": client, "socket": docker_host, "message": f"Connected using DOCKER_HOST ({docker_host})."}
            except Exception:
                pass

    # 4) Try common known locations (including user-specific ones)
    for p in COMMON_SOCKETS:
        candidate = os.path.expanduser(p)
        if os.path.exists(candidate):
            client = _try_client_with_socket(candidate)
            if client:
                return {"status": "connected", "client": client, "socket": candidate, "message": f"Connected using common socket path: {candidate}"}

    # 5) Do a safe shallow search across likely directories (no sudo, limited depth)
    found = _safe_search_socket(max_depth=4)
    if found:
        client = _try_client_with_socket(found)
        if client:
            return {"status": "connected", "client": client, "socket": found, "message": f"Connected using discovered socket path: {found}"}
        else:
            return {"status": "error", "client": None, "socket": found, "message": f"Found socket at {found} but couldn't contact daemon (permission or daemon down)."}

    # 6) Final helpful diagnostics
    # Check if docker binary exists
    docker_bin = shutil_which("docker")
    if not docker_bin:
        return {"status": "error", "client": None, "socket": None, "message": "Docker CLI not found in PATH. Is Docker installed?"}

    # If docker CLI exists but we couldn't connect: suggest starting Docker Desktop / Engine or adding user to docker group
    return {
        "status": "error",
        "client": None,
        "socket": None,
        "message": "Docker appears installed but no accessible socket found and docker.from_env() failed. Try starting Docker Desktop/Engine or check DOCKER_HOST and permissions (e.g., add your user to the 'docker' group)."
    }

# small helper since shutil.which isn't imported above:
def shutil_which(cmd: str) -> Optional[str]:
    import shutil
    return shutil.which(cmd)


# result = get_docker_client()
# print(result)