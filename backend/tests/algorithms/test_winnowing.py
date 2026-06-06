from app.algorithms.winnowing import Winnowing, WinnowingSimilarity


def test_fingerprints_are_deterministic() -> None:
    w = Winnowing(k=3, window=3)
    tokens = ["a", "b", "c", "d", "e", "f", "g"]
    assert w.fingerprints(tokens) == w.fingerprints(tokens)


def test_identical_streams_match_fully() -> None:
    sim = WinnowingSimilarity(k=3, window=3)
    tokens = ["if", "expr", "block", "return", "expr", "call", "id"]
    assert sim.similarity(tokens, tokens).score == 1.0


def test_short_stream_still_fingerprinted() -> None:
    w = Winnowing(k=5, window=4)
    assert w.fingerprints(["a", "b"]) != set()


def test_empty_stream_has_no_fingerprints() -> None:
    assert Winnowing().fingerprints([]) == set()


def test_reordered_blocks_share_some_fingerprints() -> None:
    sim = WinnowingSimilarity(k=2, window=2)
    a = ["x", "y", "z", "p", "q", "r"]
    b = ["p", "q", "r", "x", "y", "z"]
    # Local k-grams survive a block swap, so similarity is clearly positive.
    assert sim.similarity(a, b).score > 0.0


def test_unrelated_streams_have_low_similarity() -> None:
    sim = WinnowingSimilarity(k=2, window=2)
    a = ["a", "b", "c", "d", "e", "f"]
    b = ["m", "n", "o", "p", "q", "r"]
    assert sim.similarity(a, b).score < 0.2
