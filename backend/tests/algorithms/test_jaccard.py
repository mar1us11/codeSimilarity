from app.algorithms.jaccard import JaccardSimilarity, jaccard_coefficient


def test_identical_sets_are_one() -> None:
    assert jaccard_coefficient({1, 2, 3}, {1, 2, 3}) == 1.0


def test_disjoint_sets_are_zero() -> None:
    assert jaccard_coefficient({1, 2}, {3, 4}) == 0.0


def test_two_empty_sets_are_identical() -> None:
    assert jaccard_coefficient(set(), set()) == 1.0


def test_partial_overlap() -> None:
    # |∩| = 2 ({2,3}), |∪| = 4 ({1,2,3,4})
    assert jaccard_coefficient({1, 2, 3}, {2, 3, 4}) == 0.5


def test_algorithm_reports_detail() -> None:
    result = JaccardSimilarity().similarity({1, 2, 3}, {2, 3, 4})
    assert result.score == 0.5
    assert result.detail["intersection"] == 2.0
    assert result.detail["union"] == 4.0
