from enum import Enum
import json
import logging
import msgspec
import niquests
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse
from wheel_filename import parse_wheel_filename


from .checksums import get_checksum, verify_checksum


logger = logging.getLogger("wheel_getter")


class Download(Enum):
    NONE = 0
    WHEEL = 1
    SDIST = 2


class Action(msgspec.Struct):
    """Description of an action (download / copy / build wheel)"""
    
    # general (required) attributes
    name: str  # package name
    version: str  # package version
    target_directory: Path  # where the wheels are collected
    python: str  # Python version
    
    # execution options
    dry_run: bool = False
    
    # task options / data
    download: Download = Download.NONE
    build: bool = False
    url: str | None = None
    source_path: Path | None = None
    wheel_name: str = ""
    wheel_size: int = 0
    wheel_hash: str = ""
    add_to_cache: bool = False
    
    # results and status information
    failed: bool = False
    message_weight: int = 0
    message: str = ""
    download_status: int = 0
    
    async def execute(self,
            session: niquests.AsyncSession,
            ) -> None:
        """Executes the action."""
        if self.dry_run:
            if self.download == Download.SDIST:
                logger.info(
                        "Would download sdist for %s from %s",
                        self.name, self.url)
            elif self.download == Download.WHEEL:
                logger.info(
                        "Would download wheel for %s from %s",
                        self.name,  self.url)
            elif self.source_path is not None:
                logger.info(
                        "Would copy wheel for %s from %s",
                        self.name, self.source_path)
            if self.build:
                logger.info(
                        "Would build wheel for %s",
                        self.name)
            return
        
        if self.download == Download.SDIST:
            data = await self.download_data(session)
            if not self.failed:
                logger.info("downloaded sdist for %s", self.name)
            await self.check_wheel(data)
            if not self.failed:
                data = await self.build_wheel(data)
            if not self.failed:
                logger.info("built wheel for %s", self.name)
        elif self.download == Download.WHEEL:
            data = await self.download_data(session)
            if not self.failed:
                await self.check_wheel(data)
            if not self.failed:
                logger.info("downloaded wheel for %s", self.name)
        else:
            data = await self.read_wheel()
            if not self.failed:
                logger.info("copied wheel for %s from %s", self.name, self.source_path)
        if not self.failed:
            await self.write_wheel(data)
            logger.info("wheel for %s written", self.name)
    
    async def download_data(self,
            session: niquests.AsyncSession,
            ) -> bytes:
        """Downloads wheel."""
        if self.url is None:
            raise ValueError("URL missing")  # for the type checker
        r = await session.get(self.url, stream=True)
        data = await r.content
        self.download_status = r.status_code or 0
        if not r.ok:
            self.failed = True
            self.message_weight = logging.ERROR
            self.message = (
                    f"download for {self.name} from {self.url} failed: "
                    f"status={r.status_code}"
                    )
            return b""
        if data is None:
            self.failed = True
            self.message_weight = logging.ERROR
            self.message = f"no data received from {self.url}"
            return b""
        return data
    
    async def build_wheel(self, data: bytes) -> bytes:
        """Builds a wheel from an sdist."""
        
        if self.url is None:
            raise ValueError(f"no URL for {self.name}")
        parsed_url = urlparse(self.url).path
        filename = Path(parsed_url).name
        
        workdir = self.target_directory.absolute() / f"tmp-{self.name}"
        if not workdir.exists():
            workdir.mkdir()
        filepath = workdir / filename
        filepath.write_bytes(data)
        
        try:
            result = subprocess.run(
                    ["uv", "build",
                        "--wheel",
                        "--no-config",
                        "--python", self.python,
                        "--out-dir", workdir / "dist",
                        filepath,
                        ],
                    capture_output=True,
                    )
            if result.returncode:
                print(result.stdout)
                print(result.stderr, file=sys.stderr)
                self.failed = True
                self.message = f"failed to build wheel for {self.name}"
                return b""
            wheel_found = False
            wheel_path = Path("")  # make pyright happy; this is always overwritten
            for path in (workdir / "dist").glob("*.whl"):
                parsed = parse_wheel_filename(path.name)
                parsed_project = parsed.project.replace("_", "-")
                if parsed_project != self.name or parsed.version != self.version:
                    print(f"{parsed_project=}, {parsed.version=} – {self.name=}, {self.version=}")
                    continue
                wheel_path = path
                wheel_found = True
                break
            if not wheel_found:
                self.failed = True
                self.message = f"no wheel for {self.name} found after build"
                return b""
            self.wheel_name = wheel_path.name
            data = wheel_path.read_bytes()
            
        finally:
            filepath.unlink(missing_ok=True)
            try:
                workdir.rmdir()
            except OSError:
                pass
        return data

    async def read_wheel(self) -> bytes:
        """Reads wheel from disk."""
        filename = self.source_path
        if not filename:
            raise ValueError("no input filename")  # make type checker happy
        data = filename.read_bytes()
        logger.debug("wheel for %s read from %s", self.name, filename)
        return data
    
    async def check_wheel(self, data: bytes) -> None:
        """Checks wheel size and hash sum."""
        if self.wheel_size and self.wheel_size != len(data):
            self.failed = True
            self.message_weight = logging.ERROR
            self.message = (
                    f"wrong wheel size detected for {self.name}: "
                    f"{len(data)} (expected: {self.wheel_size})"
                    )
            return
        if self.wheel_hash and not verify_checksum(data, self.wheel_hash):
            self.failed = True
            self.message_weight = logging.ERROR
            self.message = f"checksum failure for {self.name}"
            return
    
    async def write_wheel(self, data: bytes) -> None:
        """Writes wheel data to target directory."""
        filename = self.target_directory / self.wheel_name
        filename.write_bytes(data)
        logger.debug("wheel %s written", filename)
        
        wheel_size = len(data)
        wheel_hash = get_checksum(data)
        wheel_name = filename.name
        metadata = {"filename": wheel_name, "hash": wheel_hash, "size": wheel_size}
        metafile = self.target_directory / f"{self.name}-{self.version}.info"
        json.dump(metadata, open(metafile, "w"))
    