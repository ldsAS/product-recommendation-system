"""
Pytest 配置和共用 fixtures
"""
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """專案根目錄"""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(project_root):
    """測試資料目錄"""
    return project_root / "tests" / "test_data"
