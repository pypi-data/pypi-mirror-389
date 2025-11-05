from __future__ import annotations

import numpy as np
import pandas as pd


def profile_dataset(filepath: str) -> tuple[int, int]:
	"""Profile the dataset at the given CSV filepath."""

	try:
		df = pd.read_csv(filepath)
	except FileNotFoundError as exc:
		print(f"File not found: {filepath}")
		raise exc

	# Display general information including null counts and dtypes.
	df.info()

	# Basic descriptive statistics from pandas.
	print(df.describe())

	# Additional numeric statistics from numpy.
	numeric_columns = df.select_dtypes(include=np.number).columns
	for column in numeric_columns:
		median_value = np.median(df[column])
		std_value = np.std(df[column])
		print(f"Column: {column}")
		print(f"  median: {median_value}")
		print(f"  std: {std_value}")

	row_count, column_count = df.shape
	return row_count, column_count
