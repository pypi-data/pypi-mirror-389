import os
import pathlib
import shutil
import subprocess

import pytest


class EnvironmentException(Exception):
    pass


def run_command(command):
    process = subprocess.run(
        command,
        check=False, capture_output=True,
    )

    if process.returncode != 0:
        raise EnvironmentException(f"Failed to run command: {command}")

    return process


@pytest.fixture
def docs_fixture(scope="function"):
    with pathlib.Path("version").open("w", encoding="utf-8") as version_file:
        version_file.write("13.666.2")

    yield

    os.chdir("/work")
    if pathlib.Path("doc/_build").exists():
        shutil.rmtree("doc/_build", ignore_errors=True)
    if pathlib.Path("version").exists():
        pathlib.Path("version").unlink()
    if pathlib.Path("dist").exists():
        shutil.rmtree("dist", ignore_errors=True)
    if pathlib.Path("Promium.egg-info").exists():
        shutil.rmtree("Promium.egg-info", ignore_errors=True)


class TestEnvironment:
    @pytest.mark.env
    @pytest.mark.skip("pass")
    def test_check_doc_command(self, docs_fixture):
        run_command(["sphinx-build", "-b", "html", "doc", "public"])
        assert pathlib.Path("public/index.html").exists(), "Not Create doc files"

    @pytest.mark.env
    def test_check_publish(self, docs_fixture):
        run_command(["python", "setup.py", "sdist"])
        run_command(["python", "-m", "twine", "check", "dist/*"])
