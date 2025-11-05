from __future__ import annotations

import re

import pandas as pd


def op_regex_replace(df: pd.DataFrame, params: dict) -> pd.DataFrame:
	col = params["column"]
	pattern = params["pattern"]
	repl = params["replace"]
	df[col] = df[col].astype(str).str.replace(pattern, repl, regex=True)
	return df


def op_drop_nulls(df: pd.DataFrame, params: dict) -> pd.DataFrame:
	return df.dropna(subset=[params["column"]])


def op_fill_nulls(df: pd.DataFrame, params: dict) -> pd.DataFrame:
	return df.fillna({params["column"]: params["value"]})


def op_rename_column(df: pd.DataFrame, params: dict) -> pd.DataFrame:
	return df.rename(columns={params["old_name"]: params["new_name"]})


def op_drop_column(df: pd.DataFrame, params: dict) -> pd.DataFrame:
	return df.drop(columns=[params["column"]])


def op_change_type(df: pd.DataFrame, params: dict) -> pd.DataFrame:
	df[params["column"]] = df[params["column"]].astype(params["new_type"])
	return df


def op_scale_minmax(df: pd.DataFrame, params: dict) -> pd.DataFrame:
	from sklearn.preprocessing import MinMaxScaler

	scaler = MinMaxScaler()
	column = params["column"]
	df[column] = scaler.fit_transform(df[[column]])
	return df


def op_one_hot_encode(df: pd.DataFrame, params: dict) -> pd.DataFrame:
	return pd.get_dummies(df, columns=[params["column"]])


TRANSFORMERS = {
	"regex_replace": op_regex_replace,
	"drop_nulls": op_drop_nulls,
	"fill_nulls": op_fill_nulls,
	"rename_column": op_rename_column,
	"drop_column": op_drop_column,
	"change_type": op_change_type,
	"scale_minmax": op_scale_minmax,
	"one_hot_encode": op_one_hot_encode,
}
