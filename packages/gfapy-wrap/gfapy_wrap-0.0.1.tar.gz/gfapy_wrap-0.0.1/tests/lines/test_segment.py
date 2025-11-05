"""Tests for segment lines."""

import gfapy
import pytest

from wgfapy.lines import segment as s_lines


@pytest.fixture
def def_line_str() -> str:
    """Give default segment str line."""
    return "S\tdefault\tACGT"


@pytest.fixture
def def_line(def_line_str: str) -> s_lines.Line:
    """Give default segment line."""
    return s_lines.Line(def_line_str)


@pytest.fixture
def def_graph(def_line_str: str) -> gfapy.Gfa:
    """Give default GFA graph."""
    return gfapy.Gfa([def_line_str])


def test_iter_lines(def_graph: gfapy.Gfa, def_line: s_lines.Line) -> None:
    """Test segment line iterator."""
    lines = list(s_lines.iter_lines(def_graph))
    assert lines == [def_line]
