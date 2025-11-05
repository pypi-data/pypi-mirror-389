import effspm
import tempfile

def test_simple():
    data = "-1 1 2 -1 2 3 -2\n"
    with tempfile.NamedTemporaryFile('w+', delete=False) as f:
        f.write(data)
        fname = f.name

    patterns = effspm.mine(fname, minsup=1)

    # Single-item patterns
    assert [1] in patterns
    assert [2] in patterns
    assert [3] in patterns

    # Two-item patterns
    assert [1, 2] in patterns
    assert [2, 3] in patterns
