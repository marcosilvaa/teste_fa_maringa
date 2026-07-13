import pandas as pd

from src.formatting import (
    dataframe_to_csv_bytes,
    format_brl,
    format_date,
    format_percentage,
    format_quantity,
)


def test_portuguese_format_examples():
    assert format_brl(7725855.07) == "R$ 7.725.855,07"
    assert format_quantity(25110) == "25.110"
    assert format_percentage(0.0929) == "9,29%"
    assert format_date(pd.Timestamp("2026-03-02")) == "02/03/2026"


def test_csv_export_uses_bom_semicolon_decimal_comma_and_portuguese_date():
    frame = pd.DataFrame({"PERIODO": [pd.Timestamp("2026-03-02")], "valor": [12.5]})
    data = dataframe_to_csv_bytes(frame)
    assert data.startswith(b"\xef\xbb\xbf")
    text = data.decode("utf-8-sig")
    assert ";" in text
    assert "02/03/2026" in text
    assert "12,5" in text
