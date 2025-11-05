import json
import os
import zipfile

from pipper import s3
from pipper import versioning
from pipper.environment import Environment


def is_already_published(env: Environment, metadata: dict) -> bool:
    """
    Determines whether or not the specified pipper bundle has been published
    already or not.

    :param env:
        Configuration data for the execution environment for this command invocation.
    :param metadata:
        Dictionary containing the metadata extracted from the pipper bundle in question.
    """
    return s3.key_exists(
        s3_client=env.s3_client,
        bucket=env.bucket,
        key=versioning.make_s3_key(
            package_name=metadata["name"],
            package_version=metadata["version"],
            root_prefix=env.root_prefix,
        ),
    )


def read_metadata(bundle_path: str) -> dict:
    """
    Reads the pipper package metadata for the specified pipper bundle.

    :param bundle_path:
        Absolute path to a pipper bundle file from which to read the metadata.
    """
    with zipfile.ZipFile(bundle_path) as zipper:
        contents = zipper.read("package.meta")

    return json.loads(contents)


def get_pipper_files_in(target_directory: str) -> list:
    """
    Retrieves the pipper bundles in the specified directory.

    :param target_directory:
        Directory in which to search for pipper package bundles to publish.
    :return:
        A list containing the paths to the pipper packages in the given directory
        sorted by modified time from oldest to most recent.
    """

    directory = os.path.realpath(target_directory)

    def to_path_entry(filename: str) -> dict:
        path = os.path.join(directory, filename)
        return {"time": os.path.getmtime(path), "path": path}

    path_entries = [
        to_path_entry(filename)
        for filename in os.listdir(directory)
        if filename.endswith(".pipper")
    ]
    path_entries.sort(key=lambda entry: entry["time"])

    return [e["path"] for e in path_entries if os.path.isfile(e["path"])]


def from_pipper_file(env: Environment, bundle_path: str):
    """
    Uploads the pipper file located in the specified bundle path.

    :param env:
        Configuration data for the execution environment for this command invocation.
    :param bundle_path:
        Directory containing a pipper package to upload. If multiple pipper packages
        exist in the directory, the one most recently created/modified will be
        uploaded.
    """
    metadata = read_metadata(bundle_path)

    print('[SYNCING]: "{}"'.format(metadata["name"]))

    force: bool = env.args.get("force") or False
    if not force and is_already_published(env, metadata):
        print(
            '[SKIPPED]: "{}" version {} is already published'.format(
                metadata["name"], metadata["version"]
            )
        )

        if env.args.get("skip_fails"):
            raise ValueError("Failed because this version and published version match.")

        return

    print('[PUBLISHING]: "{}" version {}'.format(metadata["name"], metadata["version"]))

    content_length = os.path.getsize(bundle_path)

    with open(bundle_path, "rb") as f:
        env.s3_client.put_object(
            # Allow overriding the ACL from the command.
            ACL=env.args.get("s3_object_acl") or "private",
            Body=f,
            Bucket=env.bucket,
            Key=versioning.make_s3_key(
                metadata["name"],
                metadata["version"],
                root_prefix=env.root_prefix,
            ),
            ContentType="application/zip",
            ContentLength=content_length,
            Metadata={
                "package": json.dumps(metadata),
                "version": metadata["version"],
                "safe_version": metadata["safe_version"],
                "name": metadata["name"],
                "timestamp": metadata["timestamp"],
            },
        )


def run(env: Environment):
    """
    Executes a publish action, which uploads the bundled pipper package to its
    remote S3 backend based on the environment and command line options.

    :param env:
        Configuration data for the execution environment for this command invocation.
    """
    target_path = os.path.realpath(env.args["target_path"])

    if not os.path.exists(target_path):
        raise FileNotFoundError('No such path "{}"'.format(target_path))

    bundle_path = (
        get_pipper_files_in(target_path)[-1]
        if os.path.isdir(target_path)
        else target_path
    )

    return from_pipper_file(env, bundle_path)
