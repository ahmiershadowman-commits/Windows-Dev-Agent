"""
Tests for environment discovery module.

Tests are mocked to avoid PowerShell/Windows-specific dependencies.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.discovery.discovery import EnvironmentDiscovery, DiscoveryError
from src.models.environment import (
    EnvironmentSnapshot,
    SystemInfo,
    VirtualizationInfo,
    DevelopmentTools,
    Runtimes,
    RuntimeInfo,
    GitConfig,
    EditorAvailability,
    PowerShellModules,
    DevDrive,
)


# Sample discovery result (as would come from PowerShell)
MOCK_DISCOVERY_OUTPUT = {
    "timestamp": datetime.now().isoformat(),
    "success": True,
    "errors": [],
    "system": {
        "os_name": "Microsoft Windows 11 Pro",
        "os_version": "10.0.22631",
        "os_build": "22631",
        "architecture": "64-bit",
        "install_date": "2024-01-01T00:00:00Z",
        "system_root": "C:\\Windows",
        "computer_name": "TEST-COMPUTER",
        "username": "testuser",
        "domain": "TESTDOMAIN",
        "processor_count": 8,
        "processor_name": "Intel(R) Core(TM) i7-1234K CPU @ 0.00GHz",
        "total_physical_memory_gb": 32.0,
        "locale": "en-US",
        "timezone": "UTC",
    },
    "virtualization": {
        "hyper_v_available": True,
        "wsl_installed": True,
        "wsl_version": "WSL 2",
        "wsl_distros": ["Ubuntu-22.04", "Debian"],
        "windows_sandbox_available": True,
        "dev_drives": [
            {
                "drive_letter": "D",
                "label": "DevDrive",
                "size_gb": 500.0,
                "free_space_gb": 400.0,
            }
        ],
    },
    "development_tools": {
        "winget_available": True,
        "chocolatey_available": True,
        "scoop_available": True,
        "git_available": True,
        "docker_available": True,
        "vscode_available": True,
        "visual_studio_available": True,
    },
    "runtimes": {
        "python": {
            "available": True,
            "version": "3.11.0",
        },
        "node": {
            "available": True,
            "version": "20.5.0",
        },
        "rust": {
            "available": True,
            "version": "1.71.0",
        },
        "golang": {
            "available": True,
            "version": "1.21.0",
        },
        "dotnet": {
            "available": True,
            "versions": ["7.0.0", "8.0.0"],
        },
    },
    "git": {
        "available": True,
        "version": "2.42.0",
        "user_name": "Test User",
        "user_email": "test@example.com",
    },
    "editors": {
        "visual_studio_code": True,
        "visual_studio": True,
        "jetbrains_rider": False,
        "jetbrains_pycharm": True,
        "jetbrains_clion": False,
    },
    "powershell_modules": {
        "count": 42,
        "modules": ["Az.Accounts", "Az.Compute", "Pester"],
    },
}


class TestEnvironmentModels:
    """Test environment model classes."""

    def test_system_info_creation(self):
        """Test SystemInfo dataclass creation."""
        sys_info = SystemInfo(
            os_name="Windows 11",
            os_version="10.0.22631",
            os_build="22631",
            architecture="64-bit",
            computer_name="TEST-PC",
        )
        assert sys_info.os_name == "Windows 11"
        assert sys_info.computer_name == "TEST-PC"

    def test_system_info_windows_11_detection(self):
        """Test Windows 11 detection."""
        sys_info = SystemInfo(
            os_name="Microsoft Windows 11 Pro",
            os_version="10.0.22631",
            os_build="22631",
            architecture="64-bit",
        )
        assert sys_info.is_windows_11()

    def test_system_info_windows_10_detection(self):
        """Test Windows 10 detection."""
        sys_info = SystemInfo(
            os_name="Microsoft Windows 10 Pro",
            os_version="10.0.19045",
            os_build="19045",
            architecture="64-bit",
        )
        assert sys_info.is_windows_10()

    def test_virtualization_info_methods(self):
        """Test VirtualizationInfo helper methods."""
        virt = VirtualizationInfo(
            hyper_v_available=True,
            wsl_installed=True,
            wsl_version="WSL 2",
            windows_sandbox_available=True,
        )
        assert virt.has_hyper_v()
        assert virt.has_wsl()
        assert virt.has_sandbox()

    def test_virtualization_info_isolation_options(self):
        """Test isolation options enumeration."""
        virt = VirtualizationInfo(
            hyper_v_available=True,
            wsl_installed=True,
            wsl_version="WSL 2",  # WSL 2 is required
            windows_sandbox_available=True,
        )
        options = virt.get_available_isolation_options()
        assert "hyper-v" in options
        assert "wsl" in options
        assert "windows-sandbox" in options

    def test_dev_drive_usage_percent(self):
        """Test Dev Drive usage percentage calculation."""
        drive = DevDrive(
            drive_letter="D",
            label="DevDrive",
            size_gb=100.0,
            free_space_gb=80.0,
        )
        assert drive.usage_percent == 20.0

    def test_development_tools_package_managers(self):
        """Test package manager enumeration."""
        tools = DevelopmentTools(
            winget_available=True,
            chocolatey_available=False,
            scoop_available=True,
        )
        managers = tools.get_available_package_managers()
        assert "winget" in managers
        assert "scoop" in managers
        assert "chocolatey" not in managers

    def test_runtimes_availability(self):
        """Test runtime availability enumeration."""
        runtimes = Runtimes(
            python=RuntimeInfo(available=True, version="3.11.0"),
            node=RuntimeInfo(available=True, version="20.5.0"),
            rust=RuntimeInfo(available=False),
            golang=RuntimeInfo(available=True, version="1.21.0"),
        )
        available = runtimes.get_available_runtimes()
        assert "python" in available
        assert "node" in available
        assert "golang" in available
        assert "rust" not in available

    def test_git_config_is_configured(self):
        """Test git configuration check."""
        git_ok = GitConfig(
            available=True,
            version="2.42.0",
            user_name="Test User",
            user_email="test@example.com",
        )
        assert git_ok.is_configured()

        git_incomplete = GitConfig(
            available=True,
            version="2.42.0",
            user_name="Test User",
            user_email=None,
        )
        assert not git_incomplete.is_configured()

    def test_editor_availability(self):
        """Test editor enumeration."""
        editors = EditorAvailability(
            visual_studio_code=True,
            visual_studio=True,
            jetbrains_pycharm=True,
        )
        available = editors.get_available_editors()
        assert "vscode" in available
        assert "visual-studio" in available
        assert "pycharm" in available

    def test_environment_snapshot_serialization(self):
        """Test EnvironmentSnapshot to_dict and from_dict."""
        snapshot = EnvironmentSnapshot(
            timestamp=datetime.now(),
            success=True,
            system=SystemInfo(
                os_name="Windows 11",
                os_version="10.0.22631",
                os_build="22631",
                architecture="64-bit",
            ),
        )
        dict_repr = snapshot.to_dict()
        assert dict_repr["success"] is True
        assert "os_name" in dict_repr["system"]

    def test_environment_snapshot_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        snapshot = EnvironmentSnapshot(
            timestamp=datetime.now(),
            success=True,
            system=SystemInfo(
                os_name="Windows 11",
                os_version="10.0.22631",
                os_build="22631",
                architecture="64-bit",
            ),
            git=GitConfig(
                available=True,
                version="2.42.0",
                user_name="Test User",
                user_email="test@example.com",
            ),
        )
        json_str = snapshot.to_json()
        snapshot2 = EnvironmentSnapshot.from_json(json_str)
        assert snapshot2.success == snapshot.success
        assert snapshot2.system.os_name == snapshot.system.os_name
        assert snapshot2.git.available == snapshot.git.available


class TestEnvironmentDiscovery:
    """Test environment discovery."""

    @patch("subprocess.run")
    def test_discovery_parse_valid_output(self, mock_run):
        """Test discovery parsing valid PowerShell output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(MOCK_DISCOVERY_OUTPUT),
            stderr="",
        )

        discovery = EnvironmentDiscovery(cache_enabled=False)
        snapshot = discovery.discover()

        assert snapshot.success is True
        assert snapshot.system.os_name == "Microsoft Windows 11 Pro"
        assert snapshot.system.processor_count == 8
        assert snapshot.virtualization.hyper_v_available is True
        assert snapshot.runtimes.python.available is True
        assert snapshot.runtimes.python.version == "3.11.0"
        assert snapshot.git.user_email == "test@example.com"

    @patch("subprocess.run")
    def test_discovery_caching(self, mock_run):
        """Test that discovery results are cached."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(MOCK_DISCOVERY_OUTPUT),
            stderr="",
        )

        discovery = EnvironmentDiscovery(cache_enabled=True)

        # First call should run discovery
        snapshot1 = discovery.discover()
        assert snapshot1.success is True

        # Second call should use cache (without running again)
        mock_run.reset_mock()
        snapshot2 = discovery.discover()
        assert snapshot2.success is True
        # Mock should not have been called again
        mock_run.assert_not_called()

    @patch("src.discovery.discovery.EnvironmentDiscovery._load_cache", return_value=None)
    @patch("subprocess.run")
    def test_discovery_force_refresh(self, mock_run, mock_cache):
        """Test forcing discovery refresh."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(MOCK_DISCOVERY_OUTPUT),
            stderr="",
        )

        discovery = EnvironmentDiscovery(cache_enabled=True)

        # First call (disable cache loading in test)
        snapshot1 = discovery.discover()
        first_call_count = mock_run.call_count

        # Force refresh should run again
        mock_run.reset_mock()
        snapshot2 = discovery.discover(force_refresh=True)
        assert mock_run.called

    @patch("subprocess.run")
    def test_discovery_powershell_not_found(self, mock_run):
        """Test fallback when PowerShell is not available."""
        mock_run.side_effect = FileNotFoundError()

        discovery = EnvironmentDiscovery(cache_enabled=False)
        snapshot = discovery.discover()

        # Should use fallback
        assert snapshot.success is False
        assert len(snapshot.errors) > 0

    @patch("subprocess.run")
    def test_discovery_invalid_json(self, mock_run):
        """Test handling of invalid JSON output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="invalid json output",
            stderr="",
        )

        discovery = EnvironmentDiscovery(cache_enabled=False)
        snapshot = discovery.discover()

        # Should use fallback
        assert snapshot.success is False

    @patch("subprocess.run")
    def test_discovery_timeout(self, mock_run):
        """Test handling of discovery timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        discovery = EnvironmentDiscovery(cache_enabled=False)

        with pytest.raises(DiscoveryError):
            discovery.discover()

    def test_discovery_snapshot_available_runtimes(self):
        """Test querying available runtimes from snapshot."""
        snapshot = EnvironmentSnapshot(
            timestamp=datetime.now(),
            success=True,
            system=SystemInfo(
                os_name="Windows 11",
                os_version="10.0.22631",
                os_build="22631",
                architecture="64-bit",
            ),
            runtimes=Runtimes(
                python=RuntimeInfo(available=True, version="3.11.0"),
                node=RuntimeInfo(available=True, version="20.5.0"),
                rust=RuntimeInfo(available=False),
            ),
        )

        available = snapshot.runtimes.get_available_runtimes()
        assert "python" in available
        assert "node" in available
        assert "rust" not in available

    def test_discovery_snapshot_available_tools(self):
        """Test querying available tools from snapshot."""
        snapshot = EnvironmentSnapshot(
            timestamp=datetime.now(),
            success=True,
            system=SystemInfo(
                os_name="Windows 11",
                os_version="10.0.22631",
                os_build="22631",
                architecture="64-bit",
            ),
            development_tools=DevelopmentTools(
                winget_available=True,
                git_available=True,
                docker_available=False,
            ),
        )

        assert snapshot.development_tools.winget_available is True
        assert snapshot.development_tools.git_available is True
        assert snapshot.development_tools.docker_available is False


class TestEnvironmentIntegration:
    """Integration tests."""

    @patch("subprocess.run")
    def test_full_discovery_workflow(self, mock_run):
        """Test complete discovery workflow."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(MOCK_DISCOVERY_OUTPUT),
            stderr="",
        )

        discovery = EnvironmentDiscovery(cache_enabled=False)
        snapshot = discovery.discover()

        # Verify all major components are populated
        assert snapshot.timestamp is not None
        assert snapshot.system.computer_name != ""
        assert len(snapshot.virtualization.get_available_isolation_options()) > 0
        assert len(snapshot.development_tools.get_available_package_managers()) > 0
        assert len(snapshot.runtimes.get_available_runtimes()) > 0
        assert snapshot.editors.get_available_editors() != []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
