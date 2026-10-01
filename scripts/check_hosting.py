"""Validate reviewed Render configuration and smoke an owned local container."""

import argparse
import base64
from http.client import HTTPException
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError
import urllib.request
import uuid

import yaml

from run_tests import PROJECT, environment_metadata, write_report


def validate_render(path):
    document = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    services = document.get("services", [])
    if len(services) != 1:
        raise AssertionError("Render must define exactly one service")
    service = services[0]
    expected = {
        "type": "web",
        "name": "scientific-palette-lab",
        "runtime": "docker",
        "plan": "0.5c-512mb",
        "branch": "main",
        "healthCheckPath": "/health",
        "numInstances": 1,
    }
    for key, value in expected.items():
        if service.get(key) != value:
            raise AssertionError(f"Render {key}: expected {value!r}, found {service.get(key)!r}")
    disk = {"name": "research-corpus", "mountPath": "/var/data", "sizeGB": 1}
    if service.get("disk") != disk:
        raise AssertionError(f"Incorrect persistent disk: {service.get('disk')}")
    expected_env = {
        "PALETTE_HOST": {"key": "PALETTE_HOST", "value": "0.0.0.0"},
        "PALETTE_DATA_DIR": {"key": "PALETTE_DATA_DIR", "value": "/var/data"},
        "PALETTE_WEB_USERNAME": {"key": "PALETTE_WEB_USERNAME", "value": "researcher"},
        "PALETTE_WEB_PASSWORD": {"key": "PALETTE_WEB_PASSWORD", "sync": False},
    }
    entries = service.get("envVars", [])
    actual = {entry.get("key"): entry for entry in entries}
    if len(entries) != 4 or actual != expected_env:
        raise AssertionError(
            "Render environment must match the four reviewed keys; password has sync:false and no literal value"
        )
    if actual["PALETTE_DATA_DIR"]["value"] != service["disk"]["mountPath"]:
        raise AssertionError("Data directory must match disk mount")
    return {
        "status": "passed",
        "path": str(path),
        "scope": "Local syntax/configuration agreement; Render deployability unverified",
    }


def docker_command(*arguments, timeout=30):
    result = subprocess.run(
        ["docker", *arguments], capture_output=True, text=True, encoding="utf-8", timeout=timeout
    )
    if result.returncode:
        raise AssertionError(
            {
                "command": ["docker", *arguments],
                "returncode": result.returncode,
                "stdout": result.stdout[-65536:],
                "stderr": result.stderr[-65536:],
            }
        )
    return result.stdout.strip()


def smoke_docker(image, report, report_path):
    detail = report["docker"]
    name = "palette-ci-" + uuid.uuid4().hex
    container = None
    detail.update(status="running", container_name=name, image=image)
    write_report(report_path, report)
    try:
        image_info = json.loads(docker_command("image", "inspect", image))[0]
        detail["image_id"] = image_info["Id"]
        detail["image_repo_digests"] = image_info.get("RepoDigests", [])
        # BuildKit may retain base layers without creating a locally tagged base image.
        build_log = Path(report_path).parent / "docker-build.log"
        digest = None
        if build_log.exists():
            match = re.search(
                r"python:3\.12-slim@(sha256:[0-9a-f]{64})",
                build_log.read_text(encoding="utf-8", errors="replace"),
            )
            if match:
                digest = match.group(1)
        detail["base_image"] = {"reference": "python:3.12-slim", "digest": digest}
        if digest is None:
            detail["base_image"]["status"] = "unknown: base digest absent from build log"
        detail["reproducibility_limit"] = "Floating Dockerfile base and dependency resolution"
        password = "public-ci-dummy-password"
        container = docker_command(
            "run",
            "--detach",
            "--name",
            name,
            "--publish",
            "127.0.0.1::8765",
            "--env",
            "PALETTE_HOST=0.0.0.0",
            "--env",
            "PORT=8765",
            "--env",
            "PALETTE_DATA_DIR=/tmp/palette-ci-data",
            "--env",
            "PALETTE_EXTERNAL_URL=https://lab.example.test",
            "--env",
            "PALETTE_WEB_USERNAME=researcher",
            "--env",
            f"PALETTE_WEB_PASSWORD={password}",
            image,
        )
        detail["container_id"] = container
        address = docker_command("port", container, "8765/tcp")
        if not address.startswith("127.0.0.1:") or "\n" in address:
            raise AssertionError(f"Unexpected Docker loopback binding: {address}")
        url = "http://" + address
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def request(path, authenticated=False):
            headers = {"Host": "lab.example.test"}
            if authenticated:
                token = base64.b64encode(f"researcher:{password}".encode()).decode()
                headers["Authorization"] = "Basic " + token
            try:
                with opener.open(
                    urllib.request.Request(url + path, headers=headers), timeout=2
                ) as response:
                    return response.status, json.load(response)
            except HTTPError as exc:
                try:
                    return exc.code, exc.read().decode("utf-8", errors="replace")
                finally:
                    exc.close()

        deadline, last_error = time.monotonic() + 30, None
        while time.monotonic() < deadline:
            try:
                if request("/health") == (200, {"status": "ok"}):
                    break
                last_error = "Unexpected health response"
            except (OSError, ValueError, HTTPException) as exc:
                last_error = repr(exc)
            time.sleep(0.1)
        else:
            raise AssertionError(f"Docker readiness timeout: {last_error}")
        detail["health"] = {"status": "passed", "body": {"status": "ok"}}
        status, _ = request("/api/state")
        if status != 401:
            raise AssertionError(f"Unauthenticated state returned {status}")
        status, state = request("/api/state", authenticated=True)
        if (
            status != 200
            or state["dataset"] != "real"
            or state["overview"]["papers"] != 0
            or state["panels"] != []
        ):
            raise AssertionError(f"Authenticated empty real corpus failed: {status}, {state}")
        detail["state"] = {
            "status": "passed",
            "unauthenticated": 401,
            "authenticated": 200,
            "real_papers": 0,
        }
        detail["runtime"] = json.loads(
            docker_command(
                "exec",
                container,
                "python",
                "-c",
                "import platform,importlib.metadata as m,json; print(json.dumps({'python':platform.python_version(),'versions':{n:m.version(n) for n in ('numpy','Pillow','scientific-palette-lab')}}))",
            )
        )
        detail["pip_freeze"] = docker_command("exec", container, "python", "-m", "pip", "freeze")
        detail["status"] = "passed"
    except Exception as exc:
        detail.update(status="failed", error=repr(exc))
    finally:
        if container:
            try:
                # docker logs writes application stderr to its own stderr channel too.
                result = subprocess.run(
                    ["docker", "logs", container],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=10,
                )
                if result.returncode:
                    raise AssertionError(f"docker logs failed: {result.stderr}")
                logs = result.stdout + "\n" + result.stderr
                logs_path = Path(report_path).with_suffix(".container.log")
                logs_path.write_text(logs, encoding="utf-8")
                detail["logs"] = str(logs_path)
                detail["log_tail"] = logs[-65536:]
            except Exception as exc:
                detail.update(status="failed", log_error=repr(exc))
            try:
                docker_command("stop", "--time", "5", container, timeout=15)
                detail["cleanup"] = (
                    "Owned container stopped; artifacts retained for runner disposal"
                )
            except Exception as exc:
                detail["stop_error"] = repr(exc)
                try:
                    docker_command("kill", container, timeout=10)
                    detail["cleanup"] = "Owned container force-stopped"
                except Exception as kill_error:
                    detail.update(status="failed", cleanup_error=repr(kill_error))
        write_report(report_path, report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--docker")
    args = parser.parse_args()
    report = {
        "status": "unfinished",
        "environment": environment_metadata(),
        "render": {"status": "unexecuted"},
        "docker": {"status": "unexecuted"},
    }
    write_report(args.report, report)
    try:
        report["render"] = validate_render(PROJECT / "render.yaml")
        if args.docker:
            smoke_docker(args.docker, report, args.report)
        report["status"] = (
            "passed" if not args.docker or report["docker"]["status"] == "passed" else "failed"
        )
    except Exception as exc:
        report.update(status="failed", error=repr(exc))
        if report["render"]["status"] == "unexecuted":
            report["render"] = {"status": "failed", "error": repr(exc)}
    write_report(args.report, report)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
