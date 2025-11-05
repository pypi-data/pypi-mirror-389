"""BAML project management and CLI wrapper."""

import asyncio
from pathlib import Path
from typing import Any

from inquire.exceptions import BamlError
from inquire.types import BamlFunction


class BamlManager:
    """Manages BAML CLI and project initialization."""

    def __init__(self, baml_dir: Path | None = None):
        """Initialize BAML manager.

        Args:
            baml_dir: Path to BAML project directory (default: cwd/baml_schemas)
        """
        self.baml_dir = baml_dir or Path.cwd() / "baml_schemas"
        self._initialized = False

    async def init(self) -> None:
        """Initialize BAML project if needed."""
        if self._initialized:
            return

        # Check if BAML project exists
        baml_src = self.baml_dir / "baml_src"
        if not baml_src.exists():
            await self._run_baml_init()

        # Run baml-cli generate to ensure types are up-to-date
        await self._run_baml_generate()

        self._initialized = True

    async def _run_baml_init(self) -> None:
        """Run 'baml init' to create project structure."""
        self.baml_dir.mkdir(parents=True, exist_ok=True)

        process = await asyncio.create_subprocess_exec(
            "baml",
            "init",
            cwd=self.baml_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise BamlError(f"BAML init failed: {stderr.decode()}")

    async def _run_baml_generate(self) -> None:
        """Run 'baml-cli generate' to generate Python types."""
        process = await asyncio.create_subprocess_exec(
            "baml-cli",
            "generate",
            "--client-type",
            "python/pydantic",
            cwd=self.baml_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise BamlError(f"BAML generate failed: {stderr.decode()}")

    def verify_function(self, baml_function: Any) -> None:
        """Verify that a BAML function is valid.

        Args:
            baml_function: BAML function callable from baml_client.b

        Raises:
            BamlError: If function is not valid
        """
        if not isinstance(baml_function, BamlFunction):
            raise BamlError(
                f"Invalid BAML function: {baml_function}. "
                "Must be a callable from baml_client.b"
            )

    def get_function_name(self, baml_function: Any) -> str:
        """Get the name of a BAML function.

        Args:
            baml_function: BAML function callable

        Returns:
            Function name as string
        """
        if hasattr(baml_function, "__name__"):
            return baml_function.__name__
        return str(baml_function)
