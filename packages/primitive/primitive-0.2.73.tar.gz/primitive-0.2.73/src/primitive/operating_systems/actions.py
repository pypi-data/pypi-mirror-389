from enum import Enum

from gql import gql
import requests

from primitive.operating_systems.graphql.mutations import (
    operating_system_create_mutation,
)
from primitive.operating_systems.graphql.queries import operating_system_list_query
from primitive.utils.actions import BaseAction
from primitive.utils.auth import guard

from primitive.utils.cache import get_operating_systems_cache
from pathlib import Path
from urllib.request import urlopen
import os
from loguru import logger

from primitive.utils.checksums import get_checksum_from_file, calculate_sha256
from primitive.utils.text import slugify


class OperatingSystems(BaseAction):
    def __init__(self, primitive):
        super().__init__(primitive)
        self.operating_systems_key_prefix = "operating-systems"
        self.remote_operating_systems = {
            "ubuntu-24-04-3": {
                "slug": "ubuntu-24-04-3",
                "iso": "https://releases.ubuntu.com/24.04.3/ubuntu-24.04.3-desktop-amd64.iso",
                "checksum": "https://releases.ubuntu.com/24.04.3/SHA256SUMS",
                "checksum_file_type": self.OperatingSystemChecksumFileType.SHA256SUMS,
            },
        }

    class OperatingSystemChecksumFileType(Enum):
        SHA256SUMS = "SHA256SUMS"

    def list_remotes(self):
        return self.remote_operating_systems.values()

    def get_remote_info(self, slug: str):
        return self.remote_operating_systems[slug]

    def _download_remote_operating_system_iso(
        self, remote_operating_system_name: str, directory: str | None = None
    ):
        cache_dir = Path(directory) if directory else get_operating_systems_cache()
        operating_system_dir = Path(cache_dir / remote_operating_system_name)
        iso_dir = Path(operating_system_dir / "iso")
        os.makedirs(iso_dir, exist_ok=True)

        operating_system_info = self.remote_operating_systems[
            remote_operating_system_name
        ]
        iso_remote_url = operating_system_info["iso"]
        iso_filename = iso_remote_url.split("/")[-1]
        iso_file_path = Path(iso_dir / iso_filename)

        if iso_file_path.exists() and iso_file_path.is_file():
            logger.info("Operating system iso already downloaded.")
            return iso_file_path

        logger.info(
            f"Downloading operating system '{remote_operating_system_name}' iso. This may take a few minutes..."
        )

        session = requests.Session()
        with session.get(iso_remote_url, stream=True) as response:
            response.raise_for_status()
            with open(iso_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        f.flush()

        logger.info(
            f"Successfully downloaded operating system iso to '{iso_file_path}'."
        )

        return iso_file_path

    def _download_remote_operating_system_checksum(
        self, remote_operating_system_name: str, directory: str | None = None
    ):
        cache_dir = Path(directory) if directory else get_operating_systems_cache()
        operating_system_dir = Path(cache_dir / remote_operating_system_name)
        checksum_dir = Path(operating_system_dir / "checksum")
        os.makedirs(checksum_dir, exist_ok=True)

        operating_system_info = self.remote_operating_systems[
            remote_operating_system_name
        ]
        checksum_filename = operating_system_info["checksum"].split("/")[-1]

        checksum_file_path = Path(checksum_dir / checksum_filename)
        if checksum_file_path.exists() and checksum_file_path.is_file():
            logger.info("Operating system checksum already downloaded.")
            return checksum_file_path

        logger.info(
            f"Downloading operating system '{remote_operating_system_name}' checksum."
        )

        checksum_response = urlopen(operating_system_info["checksum"])
        checksum_file_content = checksum_response.read()
        with open(checksum_file_path, "wb") as f:
            f.write(checksum_file_content)

        logger.info(f"Successfully downloaded checksum to '{checksum_file_path}'.")

        return checksum_file_path

    def download_remote(
        self, remote_operating_system_name: str, directory: str | None = None
    ):
        remote_operating_system_names = list(self.remote_operating_systems.keys())

        if remote_operating_system_name not in remote_operating_system_names:
            logger.error(
                f"No such operating system '{remote_operating_system_name}'. Run 'primitive operating-systems list' for available operating systems."
            )
            raise ValueError(
                f"No such operating system '{remote_operating_system_name}'."
            )

        iso_file_path = self._download_remote_operating_system_iso(
            remote_operating_system_name,
            directory=directory,
        )
        checksum_file_path = self._download_remote_operating_system_checksum(
            remote_operating_system_name,
            directory=directory,
        )

        logger.info("Validating iso checksum")
        checksum_valid = self.primitive.operating_systems._validate_checksum(
            remote_operating_system_name, str(iso_file_path), str(checksum_file_path)
        )

        if not checksum_valid:
            raise Exception(
                "Checksums did not match:  file may have been corrupted during download."
                + f"\nTry deleting the directory {get_operating_systems_cache()}/{remote_operating_system_name} and running this command again."
            )

        logger.info("Checksum valid")

        return iso_file_path, checksum_file_path

    def _validate_checksum(
        self,
        operating_system_name: str,
        iso_file_path: str,
        checksum_file_path: str,
        checksum_file_type: OperatingSystemChecksumFileType | None = None,
    ):
        checksum_file_type = (
            checksum_file_type
            if checksum_file_type
            else self.get_remote_info(operating_system_name)["checksum_file_type"]
        )

        match checksum_file_type:
            case self.OperatingSystemChecksumFileType.SHA256SUMS:
                return self._validate_sha256_sums_checksum(
                    iso_file_path, checksum_file_path
                )
            case _:
                logger.error(f"Invalid checksum file type: {checksum_file_type}")
                raise ValueError(f"Invalid checksum file type: {checksum_file_type}")

    def _validate_sha256_sums_checksum(self, iso_file_path, checksum_file_path):
        iso_file_name = Path(iso_file_path).name

        remote_checksum = get_checksum_from_file(checksum_file_path, iso_file_name)
        local_checksum = calculate_sha256(iso_file_path)
        return remote_checksum == local_checksum

    def _upload_iso_file(
        self, iso_file_path: Path, organization_id: str, operating_system_slug: str
    ):
        iso_upload_result = self.primitive.files.upload_file_direct(
            path=iso_file_path,
            organization_id=organization_id,
            key_prefix=f"{self.operating_systems_key_prefix}/{operating_system_slug}",
        )

        if not iso_upload_result or iso_upload_result.data is None:
            logger.error("Unable to upload iso file")
            raise Exception("Unable to upload iso file")

        iso_upload_data = iso_upload_result.data
        iso_file_id = iso_upload_data.get("fileUpdate", {}).get("id")

        if not iso_file_id:
            logger.error("Unable to upload iso file")
            raise Exception("Unable to upload iso file")

        return iso_file_id

    def _upload_checksum_file(
        self, checksum_file_path: Path, organization_id: str, operating_system_slug: str
    ):
        checksum_upload_response = self.primitive.files.upload_file_via_api(
            path=checksum_file_path,
            organization_id=organization_id,
            key_prefix=f"{self.operating_systems_key_prefix}/{operating_system_slug}",
        )

        if not checksum_upload_response.ok:
            logger.error("Unable to upload checksum file")
            raise Exception("Unable to upload checksum file")

        checksum_file_id = (
            checksum_upload_response.json()
            .get("data", {})
            .get("fileUpload", {})
            .get("id", {})
        )

        if not checksum_file_id:
            logger.error("Unable to upload checksum file")
            raise Exception("Unable to upload checksum file")

        return checksum_file_id

    @guard
    def create(
        self,
        slug: str,
        iso_file: str,
        checksum_file: str,
        checksum_file_type: str,
        organization_id: str,
        is_global: bool = False,
    ):
        formatted_slug = slugify(slug)
        is_slug_available = self.primitive.operating_systems._is_slug_available(
            slug=formatted_slug,
            organization_id=organization_id,
        )

        if not is_slug_available:
            raise Exception(
                f"Operating system with slug {formatted_slug} already exists."
            )

        is_known_checksum_file_type = (
            checksum_file_type
            in self.primitive.operating_systems.OperatingSystemChecksumFileType._value2member_map_
        )

        if not is_known_checksum_file_type:
            raise Exception(
                f"Operating system checksum file type {checksum_file_type} is not supported."
                + f" Supported types are: {''.join([type.value for type in self.primitive.operating_systems.OperatingSystemChecksumFileType])}"
            )

        iso_file_path = Path(iso_file)
        checksum_file_path = Path(checksum_file)

        if not iso_file_path.is_file():
            raise Exception(
                f"ISO file {iso_file_path} does not exist or is not a file."
            )

        if not checksum_file_path.is_file():
            raise Exception(
                f"Checksum file {checksum_file_path} does not exist or is not a file."
            )

        logger.info("Uploading iso file. This may take a while...")
        iso_file_id = self.primitive.operating_systems._upload_iso_file(
            iso_file_path=iso_file_path,
            organization_id=organization_id,
            operating_system_slug=formatted_slug,
        )

        logger.info("Uploading checksum file")
        checksum_file_id = self.primitive.operating_systems._upload_checksum_file(
            checksum_file_path=checksum_file_path,
            organization_id=organization_id,
            operating_system_slug=formatted_slug,
        )

        logger.info("Creating operating system in primitive.")
        operating_system_create_response = (
            self.primitive.operating_systems._create_query(
                slug=formatted_slug,
                checksum_file_id=checksum_file_id,
                checksum_file_type=checksum_file_type,
                organization_id=organization_id,
                iso_file_id=iso_file_id,
                is_global=is_global,
            )
        )

        if "id" not in operating_system_create_response:
            raise Exception("Failed to create operating system")

        return operating_system_create_response

    @guard
    def _create_query(
        self,
        slug: str,
        organization_id: str,
        checksum_file_id: str,
        checksum_file_type: str,
        iso_file_id: str,
        is_global: bool = False,
    ):
        mutation = gql(operating_system_create_mutation)
        input = {
            "slug": slug,
            "organizationId": organization_id,
            "checksumFileId": checksum_file_id,
            "checksumFileType": checksum_file_type,
            "isoFileId": iso_file_id,
            "isGlobal": is_global,
        }
        variables = {"input": input}
        result = self.primitive.session.execute(
            mutation, variable_values=variables, get_execution_result=True
        )
        return result.data.get("operatingSystemCreate")

    @guard
    def list(
        self,
        organization_id: str,
        slug: str | None = None,
        id: str | None = None,
    ):
        query = gql(operating_system_list_query)

        variables = {
            "filters": {
                "organization": {"id": organization_id},
            }
        }

        if slug:
            variables["filters"]["slug"] = {"exact": slug}

        if id:
            variables["filters"]["id"] = id

        result = self.primitive.session.execute(
            query, variable_values=variables, get_execution_result=True
        )

        edges = result.data.get("operatingSystemList").get("edges", [])

        nodes = [edge.get("node") for edge in edges]

        return nodes

    @guard
    def download(
        self,
        organization_id: str,
        id: str | None = None,
        slug: str | None = None,
        directory: str | None = None,
    ):
        operating_system = self.primitive.operating_systems.get(
            organization_id=organization_id, slug=slug, id=id
        )

        is_cached = self.primitive.operating_systems.is_operating_system_cached(
            slug=operating_system["slug"],
            directory=directory,
        )

        if is_cached:
            raise Exception(
                "Operating system already exists in cache, aborting download."
            )

        download_directory = (
            Path(directory) / operating_system["slug"]
            if directory
            else (get_operating_systems_cache() / operating_system["slug"])
        )
        checksum_directory = download_directory / "checksum"
        checksum_file_path = (
            checksum_directory / operating_system["checksumFile"]["fileName"]
        )
        iso_directory = download_directory / "iso"
        iso_file_path = iso_directory / operating_system["isoFile"]["fileName"]

        if not iso_directory.exists():
            iso_directory.mkdir(parents=True)

        if not checksum_directory.exists():
            checksum_directory.mkdir(parents=True)

        logger.info("Downloading operating system iso")
        self.primitive.files.download_file(
            file_id=operating_system["isoFile"]["id"],
            output_path=iso_directory,
            organization_id=organization_id,
        )

        logger.info("Downloading operating system checksum")
        self.primitive.files.download_file(
            file_id=operating_system["checksumFile"]["id"],
            output_path=checksum_directory,
            organization_id=organization_id,
        )

        logger.info("Validating iso checksum")
        checksum_file_type = (
            self.primitive.operating_systems.OperatingSystemChecksumFileType[
                operating_system["checksumFileType"]
            ]
        )
        checksum_valid = self.primitive.operating_systems._validate_checksum(
            operating_system["slug"],
            iso_file_path,
            checksum_file_path,
            checksum_file_type=checksum_file_type,
        )

        if not checksum_valid:
            raise Exception(
                "Checksums did not match:  file may have been corrupted during download."
                + f"\nTry deleting the directory {get_operating_systems_cache()}/{operating_system['slug']} and running this command again."
            )

        return download_directory

    @guard
    def get(self, organization_id: str, slug: str | None = None, id: str | None = None):
        if not (slug or id):
            raise Exception("Slug or id must be provided.")
        if slug and id:
            raise Exception("Only one of slug or id must be provided.")

        operating_systems = self.list(organization_id=organization_id, slug=slug, id=id)

        if len(operating_systems) == 0:
            if slug:
                logger.error(f"No operating system found for slug '{slug}'.")
                raise Exception(f"No operating system  found for slug {slug}.")
            else:
                logger.error(f"No operating system found for ID {id}.")
                raise Exception(f"No operating system  found for ID {id}.")

        return operating_systems[0]

    @guard
    def _is_slug_available(self, slug: str, organization_id: str):
        query = gql(operating_system_list_query)

        variables = {
            "filters": {
                "slug": {"exact": slug},
                "organization": {"id": organization_id},
            }
        }

        result = self.primitive.session.execute(
            query, variable_values=variables, get_execution_result=True
        )

        count = result.data.get("operatingSystemList").get("totalCount")

        return count == 0

    def is_operating_system_cached(self, slug: str, directory: str | None = None):
        cache_dir = Path(directory) if directory else get_operating_systems_cache()
        cache_path = cache_dir / slug

        return cache_path.exists()
