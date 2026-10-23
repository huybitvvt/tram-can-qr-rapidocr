from decimal import Decimal

from tramcan_rapidocr.decision import Observation,decide


def test_conflicting_crops_are_rejected_even_with_high_scores():
    assert decide([Observation('1.20',.99,'a'),Observation('12.00',.98,'b')]).value is None


def test_missing_decimal_cannot_shift_real_weight():
    assert decide([Observation('1200',.99,'a')]).value is None


def test_weak_extra_character_does_not_override_complete_reading():
    assert decide([Observation('0.42',.98,'a'),Observation('0422',.15,'b')]).value==Decimal('0.42')


def test_zero_and_negative_are_real_readings():
    assert decide([Observation('0.00',.99,'a')]).value==Decimal('0.00')
    assert decide([Observation('-0.35',.99,'a')]).value==Decimal('-0.35')


def test_profile_does_not_hide_conflicting_digit_counts():
    observations = [Observation('120',.99,'a'),Observation('1200',.99,'b')]
    assert decide(observations,fixed_digits=True).value is None


def test_confident_enhancement_cannot_override_plausible_original():
    observations = [Observation('706',.836,'original'),Observation('206',.96,'green-clahe')]
    assert decide(observations,fixed_digits=True).value is None
