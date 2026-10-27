"""Build Scaffoldlane and optionally publish only the current version."""

import argparse
import os
from pathlib import Path
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PUBLISH_ENV_FILE = ROOT / ".env.publish"


def publish_environment() -> dict[str, str]:
    if not PUBLISH_ENV_FILE.is_file():
        raise SystemExit(f"Missing {PUBLISH_ENV_FILE}. Copy .env.publish.example and fill it in.")

    values: dict[str, str] = {}
    for line in PUBLISH_ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip().strip('"\'')

    username = values.get("PYPI_USERNAME", "").strip()
    token = values.get("PYPI_TOKEN", "").strip()
    if not username or not token:
        raise SystemExit("Set PYPI_USERNAME and PYPI_TOKEN in .env.publish.")

    env = os.environ.copy()
    # uv treats --token and --username as mutually exclusive. With a username,
    # a PyPI API token is supplied as the password instead.
    env.pop("UV_PUBLISH_TOKEN", None)
    env["UV_PUBLISH_USERNAME"] = username
    env["UV_PUBLISH_PASSWORD"] = token
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--publish", action="store_true", help="Upload the built wheel and source archive to PyPI."
    )
    args = parser.parse_args()
    publish_env = publish_environment() if args.publish else None

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    name = project["name"].replace("-", "_")
    version = project["version"]
    output = ROOT / "dist" / "releases" / version

    subprocess.run(
        ["uv", "build", "--no-sources", "--out-dir", str(output)],
        cwd=ROOT,
        check=True,
    )
    wheel = output / f"{name}-{version}-py3-none-any.whl"
    source = output / f"{name}-{version}.tar.gz"
    for artifact in (wheel, source):
        if not artifact.is_file():
            raise SystemExit(f"Expected build artifact is missing: {artifact}")

    if args.publish:
        result = subprocess.run(
            ["uv", "publish", str(wheel), str(source)], cwd=ROOT, env=publish_env, check=False
        )
        if result.returncode:
            raise SystemExit(
                f"Publishing failed for version {version}. If PyPI reports that a file already "
                "exists, increment the version in pyproject.toml and retry."
            )
    else:
        print(f"Built {wheel} and {source}")
        print("Run 'python scripts/release.py --publish' to upload this version.")


if __name__ == "__main__":
    main()
