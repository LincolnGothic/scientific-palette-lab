"""Read-only archive audit and clean installed-wheel acceptance checks."""

import argparse
from email.parser import BytesParser
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import venv
import zipfile

from packaging.requirements import Requirement

from run_tests import PROJECT, clean_environment, environment_metadata, write_report

ASSETS = ("index.html", "app.js", "style.css")
VERSION = "0.1.0"


def inspect_archives(dist):
    wheels, sdists = sorted(dist.glob("*.whl")), sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise AssertionError(
            f"Expected exactly one wheel and sdist; found {sorted(p.name for p in dist.iterdir())}"
        )
    wheel, sdist = wheels[0], sdists[0]
    expected = {
        path.relative_to(PROJECT).as_posix(): path.read_bytes()
        for path in (PROJECT / "palette_lab").rglob("*.py")
    }
    expected.update(
        {
            f"palette_lab/web/{name}": (PROJECT / "palette_lab/web" / name).read_bytes()
            for name in ASSETS
        }
    )
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise AssertionError("Duplicate wheel archive members")
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise AssertionError(f"Ambiguous wheel metadata: {metadata_names}")
        metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
        for name, content in expected.items():
            if not content or archive.read(name) != content:
                raise AssertionError(f"Wheel/source mismatch: {name}")
        entry_points = archive.read(
            metadata_names[0].replace("METADATA", "entry_points.txt")
        ).decode()
        if "palette-lab = palette_lab.__main__:main" not in entry_points:
            raise AssertionError("Missing palette-lab console entry point")
    with tarfile.open(sdist, "r:gz") as archive:
        members = archive.getmembers()
        roots = {member.name.split("/")[0] for member in members}
        if len(roots) != 1:
            raise AssertionError(f"Ambiguous sdist root: {roots}")
        root = roots.pop()
        for name, content in expected.items():
            member = archive.getmember(f"{root}/{name}")
            if not member.isfile():
                raise AssertionError(f"Not a regular sdist resource: {name}")
            with archive.extractfile(member) as resource:
                if resource.read() != content:
                    raise AssertionError(f"Sdist/source mismatch: {name}")
        with archive.extractfile(f"{root}/PKG-INFO") as resource:
            source_metadata = BytesParser().parsebytes(resource.read())
        entries = [m for m in members if m.name.endswith(".egg-info/entry_points.txt")]
        if len(entries) != 1:
            raise AssertionError("Missing/ambiguous sdist console entry point")
        with archive.extractfile(entries[0]) as resource:
            if "palette-lab = palette_lab.__main__:main" not in resource.read().decode():
                raise AssertionError("Incorrect sdist console entry point")
    for message in (metadata, source_metadata):
        if message["Name"] != "scientific-palette-lab" or message["Version"] != VERSION:
            raise AssertionError("Incorrect distribution name/version")
        if message["Requires-Python"] != ">=3.10":
            raise AssertionError("Incorrect Python requirement")
    requirements = metadata.get_all("Requires-Dist", [])
    if sorted(requirements) != sorted(source_metadata.get_all("Requires-Dist", [])):
        raise AssertionError("Wheel/sdist requirements disagree")
    runtime = [
        Requirement(value)
        for value in requirements
        if not Requirement(value).marker or Requirement(value).marker.evaluate()
    ]
    if {item.name.lower(): str(item.specifier) for item in runtime} != {
        "numpy": ">=1.24",
        "pillow": ">=10.1",
    }:
        raise AssertionError(f"Unexpected declared runtime requirements: {requirements}")
    return (
        wheel,
        {
            "status": "passed",
            "wheel": str(wheel),
            "sdist": str(sdist),
            "resources": sorted(expected),
            "requires_dist": requirements,
        },
        [str(item) for item in runtime],
    )


def verify(dist, report_path):
    report_path = Path(report_path).resolve()
    report = {"status": "unfinished", "environment": environment_metadata(), "checks": {}}
    checks = report["checks"]
    for name in (
        "build",
        "archives",
        "venv",
        "install",
        "origin",
        "resources",
        "help",
        "demo",
        "server",
        "unit_suite",
    ):
        checks[name] = {"status": "unexecuted"}
    # Build is a preceding CI step; archive presence alone cannot attest its execution.
    checks["build"] = {"status": "external", "command": "python -m build --no-isolation"}
    write_report(report_path, report)
    stage = "archives"
    try:
        wheel, checks["archives"], runtime = inspect_archives(dist)
        write_report(report_path, report)
        stage = "venv"
        root = Path(
            tempfile.mkdtemp(
                prefix="palette-distribution-", dir=os.environ.get("RUNNER_TEMP") or PROJECT.parent
            )
        )
        if root.resolve().is_relative_to(PROJECT):
            raise AssertionError("Clean runtime must be outside checkout")
        work = root / "work"
        work.mkdir()
        runtime_venv = root / "venv"
        report.update(
            artifact_root=str(root),
            cleanup="Owned artifacts retained; runner disposal handles CI artifacts",
        )
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(runtime_venv)
        scripts = runtime_venv / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        env = clean_environment()
        env["PALETTE_TEST_CWD"] = str(work)
        env["PATH"] = str(scripts) + os.pathsep + env["PATH"]
        checks["venv"] = {
            "status": "passed",
            "path": str(runtime_venv),
            "system_site_packages": False,
        }

        def command(arguments, timeout=30):
            result = subprocess.run(
                [str(arg) for arg in arguments],
                cwd=work,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
            )
            detail = {
                "command": [str(arg) for arg in arguments],
                "returncode": result.returncode,
                "stdout": result.stdout[-65536:],
                "stderr": result.stderr[-65536:],
            }
            checks[stage].setdefault("commands", []).append(detail)
            write_report(report_path, report)
            if result.returncode:
                raise AssertionError(detail)
            return result.stdout

        stage = "install"
        command(
            [
                python,
                "-I",
                "-m",
                "pip",
                "install",
                "-c",
                PROJECT / "ci/constraints.txt",
                "--only-binary=numpy,Pillow",
                *runtime,
            ],
            timeout=180,
        )
        command([python, "-I", "-m", "pip", "check"])
        command([python, "-I", "-m", "pip", "install", "--no-deps", wheel], timeout=60)
        command([python, "-I", "-m", "pip", "check"])
        checks[stage]["pip_freeze"] = command([python, "-I", "-m", "pip", "freeze"])
        command(
            [
                python,
                "-I",
                "-c",
                "import importlib.metadata as m; names={d.metadata['Name'].lower() for d in m.distributions()}; assert not names & {'build','ruff','pyyaml','wheel','packaging','pyproject-hooks'}, names",
            ]
        )
        checks[stage]["status"] = "passed"
        stage = "origin"
        origin = command(
            [
                python,
                "-I",
                "-c",
                "import json, palette_lab, sys; print(json.dumps({'package': palette_lab.__file__, 'prefix': sys.prefix, 'path': sys.path}))",
            ]
        )
        checks[stage]["detail"] = json.loads(origin)
        location = Path(checks[stage]["detail"]["package"]).resolve()
        if not location.is_relative_to(runtime_venv.resolve()) or location.is_relative_to(PROJECT):
            raise AssertionError(f"Source checkout masked installed package: {location}")
        checks[stage]["status"] = "passed"
        stage = "resources"
        resource_json = command(
            [
                python,
                "-I",
                "-c",
                "import importlib.resources as r, json; print(json.dumps({n:r.files('palette_lab').joinpath('web',n).read_bytes().hex() for n in ('index.html','app.js','style.css')}))",
            ]
        )
        for name, content in json.loads(resource_json).items():
            if bytes.fromhex(content) != (PROJECT / "palette_lab/web" / name).read_bytes():
                raise AssertionError(f"Installed/source resource mismatch: {name}")
        checks[stage]["status"] = "passed"
        stage = "help"
        command([python, "-I", "-m", "palette_lab", "--help"], timeout=10)
        command(
            [scripts / ("palette-lab.exe" if os.name == "nt" else "palette-lab"), "--help"],
            timeout=10,
        )
        checks[stage]["status"] = "passed"
        stage = "demo"
        demo = work / "demo"
        command([python, "-I", "-m", "palette_lab", "--data-dir", demo, "demo"], timeout=30)
        command(
            [
                python,
                "-I",
                "-c",
                "import sqlite3,sys; db=sqlite3.connect(sys.argv[1]); assert db.execute('SELECT COUNT(*) FROM papers WHERE is_demo=1').fetchone()[0]==12; assert db.execute('SELECT COUNT(*) FROM papers WHERE is_demo=0').fetchone()[0]==0; db.close()",
                demo / "corpus.sqlite3",
            ]
        )
        checks[stage].update(status="passed", demo_records=12, real_papers=0)
        stage = "server"
        sys.path.insert(0, str(PROJECT / "tests"))
        from support import running_server

        data = work / "server"
        data.mkdir()
        with running_server(
            [
                str(python),
                "-I",
                "-X",
                "utf8",
                "-u",
                "-m",
                "palette_lab",
                "--data-dir",
                str(data),
                "serve",
                "--port",
                "0",
                "--host",
                "127.0.0.1",
            ],
            work,
            data,
            env,
        ) as (url, diagnostics):
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(url + "/api/state", timeout=5) as response:
                state = json.load(response)
                if state["overview"]["papers"] != 0 or state["panels"] != []:
                    raise AssertionError(diagnostics())
            for name in ASSETS:
                route = "/" if name == "index.html" else "/" + name
                with opener.open(url + route, timeout=5) as response:
                    if response.read() != (PROJECT / "palette_lab/web" / name).read_bytes():
                        raise AssertionError(
                            f"Installed server resource mismatch: {name}\n{diagnostics()}"
                        )
        checks[stage].update(status="passed", data_directory=str(data))
        stage = "unit_suite"
        suite_report = report_path.with_name(report_path.stem + ".installed-tests.json")
        command(
            [
                python,
                "-I",
                PROJECT / "scripts/run_tests.py",
                "--timeout",
                "180",
                "--report",
                suite_report,
            ],
            # The bounded watchdog owns worker cleanup; an outer deadline could kill it first.
            timeout=None,
        )
        checks[stage].update(
            status="passed",
            report=str(suite_report),
            result=json.loads(suite_report.read_text(encoding="utf-8")),
        )
        report["status"] = "passed"
    except Exception as exc:
        checks[stage].update(
            status="timeout" if isinstance(exc, subprocess.TimeoutExpired) else "failed",
            error=repr(exc),
        )
        report["status"] = "failed"
    write_report(report_path, report)
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    dist = args.dist if args.dist.is_absolute() else PROJECT / args.dist
    return verify(dist.resolve(), args.report)


if __name__ == "__main__":
    sys.exit(main())
