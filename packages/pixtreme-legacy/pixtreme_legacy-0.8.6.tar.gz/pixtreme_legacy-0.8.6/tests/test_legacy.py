"""Tests for pixtreme-legacy package."""

import pytest


def test_all_exports():
    """Test that all expected functions are exported."""
    import pixtreme_legacy

    expected_exports = [
        "apply_lut_cp",
        "uyvy422_to_ycbcr444_cp",
        "ndi_uyvy422_to_ycbcr444_cp",
        "yuv420p_to_ycbcr444_cp",
        "yuv422p10le_to_ycbcr444_cp",
    ]

    for name in expected_exports:
        assert hasattr(pixtreme_legacy, name), f"Missing export: {name}"


def test_functions_are_callable():
    """Test that all exported functions are callable."""
    import pixtreme_legacy

    for name in pixtreme_legacy.__all__:
        if name != "__version__":
            func = getattr(pixtreme_legacy, name)
            assert callable(func), f"{name} is not callable"


def test_readme_exists():
    """Test that README.md exists in the legacy package."""
    import pathlib

    legacy_dir = pathlib.Path(__file__).parent.parent
    readme_path = legacy_dir / "README.md"
    assert readme_path.exists(), "README.md not found"
    assert readme_path.stat().st_size > 0, "README.md is empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
