"""Utility functions."""
import logging
import os
from argparse import ArgumentParser
from glob import glob
from zipfile import ZipFile

from github3 import login

from . import __version__

logger = logging.getLogger(__name__)


def add_standard_arguments(parser: ArgumentParser):
    """Add a set of standard command-line arguments to the given ``parser``.

    Currently, the standard consists of:
    • ``--version``, to give the standard version metadata
    """
    parser.add_argument("--version", action="version", version=__version__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const=logging.DEBUG,
        default=logging.INFO,
        dest="loglevel",
        help="Log copious debugging messages suitable for developers",
    )
    group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=logging.WARNING,
        dest="loglevel",
        help="Don't log anything except warnings and critically-important messages",
    )


def get_latest_release(token, org, repo, github_object=None):
    """Get latest release from repository."""
    if not github_object:
        github_object = login(token=token)

    repo = github_object.repository(org, repo)
    return repo.latest_release()


def convert_pds4_version_to_alpha(pds4_version):
    """Convert PDS4 number version to 4 alphanumeric character version.

    For example: 1.21.0.0 to 1K00
    """
    pds4_version_short = ""
    version_list = pds4_version.split(".")
    for num in version_list:
        if int(num) >= 10:
            pds4_version_short += chr(ord("@") + (int(num) - 9))
        else:
            pds4_version_short += num

    return pds4_version_short


class Assets:
    """Assets."""

    @staticmethod
    def download_asset(release, output_path, startswith="", file_extension=""):
        """Download asset from GitHub."""
        _output = None
        for _asset in release.assets():
            # print(a.name)

            if _asset.name.startswith(startswith) and _asset.name.endswith(file_extension):
                logger.info(f"Downloading asset {_asset.name}")
                _output = os.path.join(output_path, _asset.name)
                _asset.download(path=_output)
                break

        return _output

    @staticmethod
    def unzip_asset(inzip, output_path):
        """Unzip Zip package of assets."""
        if not os.path.exists(inzip):
            raise Exception(f'Github Asset "{inzip}" not found. Check release.')

        if not os.path.exists(output_path):
            raise Exception(f'Output path "{output_path}" not found.')

        logger.info(f"Unzipping asset {inzip}")
        with ZipFile(inzip, "r") as _zip_ref:
            _zip_ref.extractall(output_path)
            _outdir = os.path.join(output_path, _zip_ref.namelist()[0])

        return _outdir

    @staticmethod
    def zip_assets(file_paths, outzip):
        """Zip assets into one package."""
        if os.path.exists(outzip):
            raise Exception(f'"{outzip}" already exists.')

        if not os.path.exists(os.path.dirname(outzip)):
            os.makedirs(os.path.dirname(outzip))

        logger.info("zipping assets")
        with ZipFile(outzip, "w") as z:
            for f in file_paths:
                z.write(f, os.path.basename(f))

        logger.info(f"zip package created: {outzip}")


class LDDs:
    """LDDs."""

    @staticmethod
    def find_dependency_ingest_ldds(ingest_ldd_src_dir):
        """Find applicable LDD dependencies to current LDD."""
        # Get any dependencies first
        dependencies_path = os.path.join(ingest_ldd_src_dir, "dependencies")
        dependency_ldds = glob(os.path.join(dependencies_path, "*", "src", "*IngestLDD*.xml"))
        logger.info(f"Dependent LDDs: {dependency_ldds}")
        return dependency_ldds

    @staticmethod
    def find_primary_ingest_ldd(ingest_ldd_src_dir):
        """Find primary ingestLDD in repo."""
        ingest_ldd = glob(os.path.join(ingest_ldd_src_dir, "*IngestLDD*.xml"))
        return ingest_ldd
