import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import zipfile
from datetime import datetime

# distutils imported after setuptools to avoid setuptools littering the screen
# with warnings about not being imported first
from distutils.core import run_setup
from distutils.dist import Distribution

import toml

from pipper import versioning
from pipper.environment import Environment


def zip_bundle(
    bundle_directory: str, output_directory: str, distribution_data: dict
) -> str:
    """
    Creates a pipper zip file from the temporarily stored meta data and wheel
    files and saves that zip file to the output directory location with the
    pipper extension.

    :param bundle_directory:
        The directory in which the bundle was assembled, which contains the
        metadata and wheel files
    :param output_directory:
        The directory where the zip bundle will be saved.
    :param distribution_data:
        Information about the package obtained during the wheel building
        process, which includes information retrieved from the setup.py
        file.

    :return
        Returns the absolute path to the created zip file.
    """

    filename = "{}-{}.pipper".format(
        distribution_data["package_name"], distribution_data["safe_version"]
    )
    zip_path = os.path.join(output_directory, filename)

    with zipfile.ZipFile(zip_path, mode="w") as zipper:
        for filename in os.listdir(bundle_directory):
            path = os.path.join(bundle_directory, filename)
            zipper.write(path, filename)

    return zip_path


def create_meta(
    package_directory: str, bundle_directory: str, distribution_data: dict
) -> str:
    """
    Creates a JSON-formatted metadata file with information about the package
    being bundled that is saved into the specified output directory.

    :param package_directory:
        Directory where the package being bundled resides
    :param bundle_directory:
        Directory where the bundle is being assembled. This is where the
        metadata file will be written.
    :param distribution_data:
        Information about the package obtained during the wheel building
        process, which includes information retrieved from the setup.py
        file.

    :return
        The absolute path to the created metadata file is returned.
    """

    config_path = os.path.join(package_directory, "pipper.json")

    try:
        with open(config_path, "r") as f:
            metadata: dict = json.load(f)
    except FileNotFoundError:
        metadata = {}

    metadata.update(
        dict(
            name=distribution_data["package_name"],
            wheel_name=distribution_data["wheel_name"],
            version=distribution_data["version"],
            safe_version=distribution_data["safe_version"],
            timestamp=datetime.utcnow().isoformat(),
        )
    )

    path = os.path.join(bundle_directory, "package.meta")

    with open(path, "w") as f:
        json.dump(metadata, f)

    return path


def _create_setup_py_wheel(setup_path: str, bundle_directory: str) -> dict:
    """
    Creates a wheel for a setup.py-based package definition.

    :param setup_path:
        Absolute path to the setup.py file from which to create a wheel.
    :param bundle_directory:
        Directory where bundling into a wheel should be carried out.
    """
    result: Distribution = run_setup(
        script_name=setup_path,
        script_args=["bdist_wheel", "--universal", "-d", bundle_directory],
    )

    # Pause to make sure OS releases wheel file before moving it
    time.sleep(1)

    wheel_files = [
        name for name in os.listdir(bundle_directory) if name.endswith(".whl")
    ]
    wheel_filename = wheel_files[0]
    wheel_path = os.path.join(bundle_directory, "package.whl")
    shutil.move(os.path.join(bundle_directory, wheel_filename), wheel_path)

    metadata = result.metadata
    return dict(
        wheel_path=wheel_path,
        wheel_name=wheel_filename,
        package_name=metadata.get_name(),
        version=metadata.get_version(),
        safe_version=versioning.serialize(metadata.get_version()),
    )


def _create_poetry_wheel(package_directory: str, bundle_directory: str) -> dict:
    """
    Creates a wheel for a poetry-based package definition.

    :param package_directory:
        Absolute path to directory in which the poetry package is defined.
    :param bundle_directory:
        Directory where bundling into a wheel should be carried out.
    """
    directory = pathlib.Path(package_directory).absolute()
    dist_directory = directory.joinpath("dist")

    starting_directory = pathlib.Path(".").absolute()
    os.chdir(package_directory)
    command = ["poetry", "build", "--format=wheel"]

    result = subprocess.run(command)
    os.chdir(starting_directory)
    result.check_returncode()

    # Pause to make sure OS releases wheel file before moving it
    time.sleep(1)

    wheel_files = [
        name for name in os.listdir(str(dist_directory)) if name.endswith(".whl")
    ]
    wheel_filename = wheel_files[0]
    wheel_path = os.path.join(bundle_directory, "package.whl")
    shutil.move(str(dist_directory.joinpath(wheel_filename)), wheel_path)

    configs = toml.loads(directory.joinpath("pyproject.toml").read_text())
    try:
        version = configs["tool"]["poetry"]["version"]
    except KeyError:
        version = configs["project"]["version"]

    try:
        name = configs["tool"]["poetry"]["name"]
    except KeyError:
        name = configs["project"]["name"]

    return dict(
        wheel_path=wheel_path,
        wheel_name=wheel_filename,
        package_name=name,
        version=version,
        safe_version=versioning.serialize(version),
    )


def create_wheel(package_directory: str, bundle_directory: str) -> dict:
    """
    Creates a universally wheel distribution of the specified package and
    saves that to the bundle directory.

    :param package_directory:
        Directory where the package being bundled resides
    :param bundle_directory:
        Directory where the bundle is being assembled. This is where the
        wheel file will be written.

    :return
        Returns a dictionary containing distribution information about the
        wheel package.
    """
    directory = pathlib.Path(package_directory).absolute()

    setup_path = directory.joinpath("setup.py")
    if setup_path.exists():
        # Assumes that "setup.py" must at least exist even if using setuptools
        # with a pyproject.toml + setup.cfg configuration.
        return _create_setup_py_wheel(str(setup_path), bundle_directory)

    pyproject_path = directory.joinpath("pyproject.toml")
    if pyproject_path.exists():
        # Assumes that a pyproject.toml without at least a shim setup.py means
        # that poetry is the build system.
        return _create_poetry_wheel(package_directory, bundle_directory)

    raise FileNotFoundError(
        'No package configuration file found in "{}"'.format(package_directory)
    )


def run(env: Environment):
    """
    Executes the bundling process on the specified package directory and saves
    the pipper bundle file in the specified output directory.

    :param env:
        Environment configuration in which this command is being executed
    """

    package_directory = env.args.get("package_directory") or "."
    output_directory = env.args.get("output_directory")

    directory = os.path.realpath(package_directory)
    if not os.path.exists(directory):
        raise NotADirectoryError('No such directory "{}"'.format(directory))

    save_directory = (
        os.path.realpath(output_directory) if output_directory else directory
    )

    bundle_directory = tempfile.mkdtemp(prefix="pipper-bundle-")

    try:
        print("[COMPILE]: Creating universal wheel")
        distribution_data = create_wheel(directory, bundle_directory)
        print("[COLLECT]: Creating package metadata")
        create_meta(directory, bundle_directory, distribution_data)
        print("[ASSEMBLE]: Creating pipper package bundle")
        path = zip_bundle(bundle_directory, save_directory, distribution_data)
        print("[BUNDLED]:", path)
    except Exception:
        raise
    finally:
        shutil.rmtree(bundle_directory)
