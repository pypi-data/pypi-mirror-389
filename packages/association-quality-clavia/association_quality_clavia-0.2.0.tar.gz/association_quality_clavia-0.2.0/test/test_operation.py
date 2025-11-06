"""."""

from association_quality_clavia import UPD_ID_LOOSE, AssociationQuality


def test_classify_case1234(aq: AssociationQuality) -> None:
    """."""
    aq.classify(0, 0, True)
    assert repr(aq) == 'AssociationQuality(TP 1 TN 0 FP 0 FN 0)'
    aq.classify(0, 1, True)
    assert repr(aq) == 'AssociationQuality(TP 1 TN 0 FP 0 FN 1)'
    aq.classify(0, -1, True)
    assert repr(aq) == 'AssociationQuality(TP 1 TN 0 FP 0 FN 2)'
    aq.classify(0, UPD_ID_LOOSE, True)
    assert repr(aq) == 'AssociationQuality(TP 1 TN 0 FP 0 FN 3)'


def test_classify_case5678(aq: AssociationQuality) -> None:
    """."""
    aq.classify(1, 2, False)
    assert repr(aq) == 'AssociationQuality(TP 0 TN 0 FP 1 FN 0)'
    aq.classify(1, -1, False)
    assert repr(aq) == 'AssociationQuality(TP 0 TN 0 FP 2 FN 0)'
    aq.classify(1, UPD_ID_LOOSE, False)
    assert repr(aq) == 'AssociationQuality(TP 0 TN 1 FP 2 FN 0)'


def test_classify_case9_10_11_12(aq: AssociationQuality) -> None:
    """."""
    aq.classify(-1, 1, False)
    assert repr(aq) == 'AssociationQuality(TP 0 TN 0 FP 1 FN 0)'
    aq.classify(-1, -1, False)
    assert repr(aq) == 'AssociationQuality(TP 0 TN 1 FP 1 FN 0)'
    aq.classify(-1, UPD_ID_LOOSE, False)
    assert repr(aq) == 'AssociationQuality(TP 0 TN 2 FP 1 FN 0)'
