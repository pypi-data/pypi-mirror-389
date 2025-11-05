from __future__ import annotations


def _merge(left: list[tuple], right: list[tuple], key_index: int) -> list[tuple]:
	"""Merge two sorted lists based on tuple element at key_index."""

	merged: list[tuple] = []
	i = j = 0

	while i < len(left) and j < len(right):
		if left[i][key_index] <= right[j][key_index]:
			merged.append(left[i])
			i += 1
		else:
			merged.append(right[j])
			j += 1

	if i < len(left):
		merged.extend(left[i:])
	if j < len(right):
		merged.extend(right[j:])

	return merged


def merge_sort(data_list: list[tuple], key_index: int) -> list[tuple]:
	"""Recursively sort data_list by the element at key_index."""

	if len(data_list) <= 1:
		return data_list

	mid = len(data_list) // 2
	left_sorted = merge_sort(data_list[:mid], key_index)
	right_sorted = merge_sort(data_list[mid:], key_index)
	return _merge(left_sorted, right_sorted, key_index)


def binary_search(sorted_data_list: list[tuple], target, key_index: int) -> int:
	"""Iterative binary search returning the index of target or -1 if not found."""

	low = 0
	high = len(sorted_data_list) - 1

	while low <= high:
		mid = (low + high) // 2
		mid_value = sorted_data_list[mid][key_index]
		if mid_value == target:
			return mid
		if mid_value < target:
			low = mid + 1
		else:
			high = mid - 1

	return -1
