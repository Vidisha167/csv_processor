from io import BytesIO

import pytest

from app.analysis import analyze_csv

SAMPLE = (
    b"id,name,email,age\n"
    b"1,Alice,alice@example.com,30\n"
    b"2,Bob,bob@example.com,\n"
    b"3,Carol,carol@example.com,41\n"
    b"3,Carol,carol@example.com,41\n"
    b"4,Dan,,28\n"
)


def test_analyze_sample_csv():
    result = analyze_csv(BytesIO(SAMPLE))
    assert result["row_count"] == 5
    assert result["column_count"] == 4
    assert result["missing_values"]["email"] == 1
    assert result["missing_values"]["age"] == 1
    assert result["total_missing"] == 2
    assert result["duplicate_rows"] == 1
    assert result["numeric_stats"]["age"]["count"] == 4
    assert result["numeric_stats"]["age"]["mean"] == 35


def test_empty_file_raises():
    with pytest.raises(Exception):
        analyze_csv(BytesIO(b""))