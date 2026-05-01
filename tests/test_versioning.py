import pytest

from app.utils.versioning import normalize_version, version_sort_key


class TestVersionSortKey:
    """Test cases for version_sort_key function."""

    def test_simple_version_parsing(self) -> None:
        """Test parsing of simple version strings."""
        assert version_sort_key("1.0.0") == (1, 0, 0)
        assert version_sort_key("2.5.3") == (2, 5, 3)

    def test_multi_part_versions(self) -> None:
        """Test versions with many parts."""
        assert version_sort_key("1.2.3.4.5") == (1, 2, 3, 4, 5)
        assert version_sort_key("10.20.30") == (10, 20, 30)

    def test_single_digit_version(self) -> None:
        """Test single digit version strings."""
        assert version_sort_key("1") == (1,)
        assert version_sort_key("9") == (9,)

    def test_two_part_version(self) -> None:
        """Test two-part version strings."""
        assert version_sort_key("1.0") == (1, 0)
        assert version_sort_key("3.2") == (3, 2)

    def test_invalid_version_returns_zero_tuple(self) -> None:
        """Test that invalid versions return (0,) as fallback."""
        assert version_sort_key("invalid") == (0,)
        assert version_sort_key("1.a.0") == (0,)
        assert version_sort_key("1.0.b") == (0,)

    def test_mixed_valid_invalid_returns_zero(self) -> None:
        """Test versions with some invalid parts."""
        assert version_sort_key("1.2.x.4") == (0,)

    def test_empty_string_returns_zero(self) -> None:
        """Test empty string returns (0,)."""
        assert version_sort_key("") == (0,)

    def test_version_comparison_ordering(self) -> None:
        """Test that returned tuples can be compared for ordering."""
        v1 = version_sort_key("1.0.0")
        v2 = version_sort_key("1.0.1")
        v3 = version_sort_key("2.0.0")
        
        assert v1 < v2 < v3

    def test_leading_zeros_still_compare_correctly(self) -> None:
        """Test versions with leading zeros in numeric parts."""
        assert version_sort_key("1.00.0") == (1, 0, 0)
        assert version_sort_key("01.02.03") == (1, 2, 3)


class TestNormalizeVersion:
    """Test cases for normalize_version function."""

    def test_normalize_standard_version(self) -> None:
        """Test normalization of standard three-part versions."""
        assert normalize_version("1.0.0") == "1.0"
        assert normalize_version("2.5.3") == "2.5"
        assert normalize_version("10.20.30") == "10.20"

    def test_normalize_two_part_version_unchanged(self) -> None:
        """Test that two-part versions remain unchanged."""
        assert normalize_version("1.0") == "1.0"
        assert normalize_version("2.5") == "2.5"

    def test_normalize_single_part_version_unchanged(self) -> None:
        """Test that single-part versions remain unchanged."""
        assert normalize_version("1") == "1"
        assert normalize_version("5") == "5"

    def test_normalize_many_part_version_takes_first_two(self) -> None:
        """Test that versions with many parts are normalized to first two."""
        assert normalize_version("1.2.3.4.5") == "1.2"
        assert normalize_version("10.20.30.40") == "10.20"

    def test_normalize_empty_string_unchanged(self) -> None:
        """Test that empty string remains unchanged."""
        assert normalize_version("") == ""

    def test_normalize_version_with_special_chars(self) -> None:
        """Test normalization with special characters in parts."""
        # Only first two parts matter, so this should work
        assert normalize_version("1.0.beta") == "1.0"
        assert normalize_version("2.5.rc1") == "2.5"

    def test_normalize_preserves_exact_first_two_parts(self) -> None:
        """Test that normalization preserves exact values of first two parts."""
        assert normalize_version("1.0") == "1.0"
        assert normalize_version("99.99") == "99.99"
        assert normalize_version("0.1") == "0.1"

    def test_normalize_version_with_leading_zeros(self) -> None:
        """Test normalization with leading zeros in parts."""
        # The function just splits and returns first two, preserving format
        assert normalize_version("01.02.03") == "01.02"
        assert normalize_version("1.0.0") == "1.0"
