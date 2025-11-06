import pytest
from joytide import banner


def test_banner_center_basic():
    out = banner("hi", border="#", padding=1, align="center")
    lines = out.splitlines()

    # should be top / middle / bottom
    assert len(lines) == 3

    # exact middle row format when centered
    assert lines[1] == "#| hi |#"

    # top border should be same length as middle row
    assert len(lines[0]) == len(lines[1])


def test_banner_left_and_right_align():
    left = banner("abc", border="*", padding=2, align="left").splitlines()[1]
    right = banner("abc", border="*", padding=2, align="right").splitlines()[1]

    # left align puts the text near start
    assert left.startswith("*|abc")

    # right align puts the text near end
    assert right.endswith("abc|*")

    # both lines should be same total length
    assert len(left) == len(right)


def test_banner_padding_zero_and_multi_char_border():
    # padding = 0 should still work
    out = banner("yo", border="><", padding=0, align="center")
    lines = out.splitlines()

    # still 3 lines
    assert len(lines) == 3

    # middle line should have no extra padding around "yo" besides the pipes
    assert lines[1] == "><|yo|><"

    # border "><" should repeat to match width
    assert set(lines[0]) <= set("><")  # only those chars show up in top border


def test_banner_invalid_inputs():
    # padding < 0 should raise
    with pytest.raises(ValueError):
        banner("x", padding=-1)

    # bad align should raise
    with pytest.raises(ValueError):
        banner("x", align="middle")

    # empty border should raise
    with pytest.raises(ValueError):
        banner("x", border="")


def test_banner_non_string_text_raises_typeerror():
    with pytest.raises(TypeError):
        banner(123)  # text must be str
