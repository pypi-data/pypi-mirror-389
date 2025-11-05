"""Testing header line module."""

import gfapy
import pytest

from wgfapy.lines import header as h_lines


@pytest.fixture
def empty_header_str() -> str:
    """Empty header str."""
    return "H"


@pytest.fixture
def empty_header(empty_header_str: str) -> h_lines.Line:
    """Empty header."""
    return h_lines.Line(empty_header_str)


@pytest.fixture
def header_with_integer_tag_str() -> str:
    """Header with integer tag str."""
    return "H\tXX:i:1"


@pytest.fixture
def header_with_integer_tag(header_with_integer_tag_str: str) -> h_lines.Line:
    """Header with integer tag."""
    return h_lines.Line(header_with_integer_tag_str)


@pytest.fixture
def graph_without_header() -> gfapy.Gfa:
    """GFA graph without header."""
    return gfapy.Gfa()


@pytest.fixture
def graph_with_header(header_with_integer_tag_str: str) -> gfapy.Gfa:
    """GFA graph with header."""
    return gfapy.Gfa([header_with_integer_tag_str])


class TestGetLine:
    """Test get header line function."""

    def test_no_header(
        self,
        graph_without_header: gfapy.Gfa,
        empty_header: h_lines.Line,
    ) -> None:
        """Test header line from a GFA graph."""
        assert h_lines.get_line(graph_without_header) == empty_header

    def test_int_tag(
        self,
        graph_with_header: gfapy.Gfa,
        header_with_integer_tag: h_lines.Line,
    ) -> None:
        """Test header line from a GFA graph."""
        assert h_lines.get_line(graph_with_header) == header_with_integer_tag
