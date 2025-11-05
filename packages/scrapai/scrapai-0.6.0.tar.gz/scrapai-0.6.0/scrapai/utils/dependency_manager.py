"""
Dependency Manager - Installs Playwright browsers and system dependencies
Simplified: Only handles Playwright (packages are auto-installed by pip)
"""

import subprocess
import sys
import importlib
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages Playwright browser and system dependency installation"""

    def __init__(self):
        """Initialize dependency manager."""
        self.is_restricted_env = self._detect_restricted_environment()

    def _detect_restricted_environment(self) -> bool:
        """
        Detect if we're in a restricted environment (Databricks, etc.).

        Returns:
            True if restricted (no sudo), False otherwise
        """
        # Check for Databricks environment
        if os.environ.get("DATABRICKS_RUNTIME_VERSION"):
            return True

        # Check for Google Colab
        if os.environ.get("COLAB_GPU"):
            return True

        return False

    def _is_playwright_installed(self) -> bool:
        """Check if Playwright package is installed."""
        try:
            importlib.import_module("playwright")
            return True
        except ImportError:
            return False

    def install_playwright_browsers(self) -> bool:
        """
        Install Playwright browser binaries (no sudo required).

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if playwright is installed
            if not self._is_playwright_installed():
                logger.warning("Playwright package not found. Install it with: pip install playwright")
                return False

            # Install browser binaries (Chromium) - no sudo needed
            logger.info("🌐 Installing Playwright browser binaries...")
            cmd = [sys.executable, "-m", "playwright", "install", "chromium"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info("✅ Successfully installed Playwright browsers")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install Playwright browsers: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ Error installing Playwright browsers: {e}")
            return False

    def install_playwright_system_deps(self) -> bool:
        """
        Install Playwright system dependencies (may require sudo on Linux).

        Returns:
            True if successful, False otherwise
        """
        if self.is_restricted_env:
            logger.info(
                "⏭️  Skipping system dependencies (restricted environment - no sudo). "
                "Browsers will work, but some features may be limited."
            )
            return False

        try:
            if not self._is_playwright_installed():
                logger.warning("Playwright package not found.")
                return False

            # Install system dependencies (requires sudo on Linux)
            logger.info("🔧 Installing Playwright system dependencies (may require sudo)...")
            cmd = [sys.executable, "-m", "playwright", "install-deps", "chromium"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info("✅ Successfully installed Playwright system dependencies")
            return True

        except subprocess.CalledProcessError as e:
            logger.warning(
                f"⚠️  Failed to install system dependencies (may need sudo): {e.stderr}\n"
                "Browsers will still work, but some features may be limited."
            )
            return False
        except Exception as e:
            logger.warning(f"⚠️  Error installing system dependencies: {e}")
            return False

    def install(self) -> Dict[str, bool]:
        """
        Install Playwright browsers and system dependencies.

        This method:
        - Installs Playwright browser binaries (no sudo needed)
        - Installs system dependencies on Linux (may require sudo, skipped if restricted)

        Returns:
            Dict with installation results
        """
        results = {}

        # Install browser binaries (always try)
        results["browsers"] = self.install_playwright_browsers()

        # Install system dependencies (only if not restricted)
        if results["browsers"]:
            results["system_deps"] = self.install_playwright_system_deps()
        else:
            results["system_deps"] = False

        # Summary
        if results["browsers"]:
            if results["system_deps"]:
                logger.info("✅ Playwright fully installed and ready!")
            else:
                logger.info("✅ Playwright browsers installed (system deps skipped)")
        else:
            logger.warning("⚠️  Playwright browser installation failed")

        return results
