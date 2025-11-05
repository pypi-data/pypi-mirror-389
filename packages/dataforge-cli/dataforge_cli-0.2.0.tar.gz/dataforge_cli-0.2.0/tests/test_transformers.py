import numpy as np
import pandas as pd

import transformers


def test_op_regex_replace():
    df = pd.DataFrame({"product": ["SKU-1"], "id": [1]})
    params = {"column": "product", "pattern": "SKU-", "replace": ""}
    updated = transformers.op_regex_replace(df.copy(), params)
    assert updated["product"].iloc[0] == "1"


def test_op_drop_nulls():
    df = pd.DataFrame({"email": [None, "a@b.com"], "id": [1, 2]})
    params = {"column": "email"}
    updated = transformers.op_drop_nulls(df, params)
    assert len(updated) == 1
    assert updated["id"].iloc[0] == 2


def test_op_fill_nulls():
    df = pd.DataFrame({"name": [None, "Alice"], "id": [1, 2]})
    params = {"column": "name", "value": "Unknown"}
    updated = transformers.op_fill_nulls(df, params)
    assert list(updated["name"]) == ["Unknown", "Alice"]


def test_op_rename_column():
    df = pd.DataFrame({"old": [1, 2]})
    params = {"old_name": "old", "new_name": "new"}
    updated = transformers.op_rename_column(df, params)
    assert "new" in updated.columns
    assert "old" not in updated.columns


def test_op_drop_column():
    df = pd.DataFrame({"keep": [1, 2], "drop": [3, 4]})
    params = {"column": "drop"}
    updated = transformers.op_drop_column(df, params)
    assert "drop" not in updated.columns
    assert "keep" in updated.columns


def test_op_change_type():
    df = pd.DataFrame({"value": ["1", "2"]})
    params = {"column": "value", "new_type": "int"}
    updated = transformers.op_change_type(df, params)
    assert updated["value"].dtype.kind in {"i", "u"}
    assert updated["value"].sum() == 3


def test_op_scale_minmax():
    df = pd.DataFrame({"score": [0.0, 10.0, 20.0]})
    params = {"column": "score"}
    updated = transformers.op_scale_minmax(df, params)
    values = updated["score"].to_numpy()
    assert np.isclose(values.min(), 0.0)
    assert np.isclose(values.max(), 1.0)


def test_op_one_hot_encode():
    df = pd.DataFrame({"color": ["red", "blue", "red"], "id": [1, 2, 3]})
    params = {"column": "color"}
    updated = transformers.op_one_hot_encode(df, params)
    assert "color_red" in updated.columns
    assert "color_blue" in updated.columns
    assert "color" not in updated.columns
