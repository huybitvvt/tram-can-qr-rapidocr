from decimal import Decimal

import pytest

from tramcan_rapidocr.parsing import parse_weight


@pytest.mark.parametrize("text,wanted", [
    ("1.20", "1.20"), ("1,20", "1.20"), ("0.00", "0.00"),
    ("11.00", "11.00"), (" 6.86 kg ", "6.86"), ("-0.35", "-0.35"),
])
def test_preserves_observed_decimal_and_repeated_digits(text, wanted):
    assert parse_weight(text) == Decimal(wanted)


@pytest.mark.parametrize("text", ["1200", "120", "1.2", "1.200", "O.00", "6.8?", "1.20 2.30", "NET 1.20", "1e2", "NaN", ""])
def test_rejects_ambiguous_or_incomplete_readings(text):
    assert parse_weight(text) is None


def test_fixed_decimal_requires_an_explicit_scale_profile():
    assert parse_weight('120') is None
    assert parse_weight('120',fixed_digits=True)==Decimal('1.20')
    assert parse_weight('0.12',fixed_digits=True)==Decimal('0.12')
    assert parse_weight('000',fixed_digits=True)==Decimal('0.00')
    assert parse_weight('1.2',fixed_digits=True) is None
