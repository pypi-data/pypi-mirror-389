import hashlib
import re
from pathlib import Path

from loguru import logger


def calculate_sha256(file_path: str) -> str:
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File '{file_path}' does not exist.")
        raise FileNotFoundError(file_path)

    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(8192), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class ChecksumNotFoundInFile(Exception):
    pass


def get_checksum_from_file(checksum_file_path: str, file_name: str) -> str | None:
    checksum_file_path = Path(checksum_file_path)

    if not checksum_file_path.exists():
        logger.error(f"File '{checksum_file_path}' does not exist.")
        raise FileNotFoundError(checksum_file_path)

    with checksum_file_path.open("r") as f:
        for line in f:
            match = re.match(r"^([a-fA-F0-9]{64})\s+\*?(.*)$", line.strip())
            if match:
                sha256_hash, current_file_name = match.groups()
                if current_file_name == file_name:
                    return sha256_hash

    logger.error(
        f"No matching checksum entry found for {file_name} in {checksum_file_path}."
    )
    raise ChecksumNotFoundInFile(checksum_file_path)
