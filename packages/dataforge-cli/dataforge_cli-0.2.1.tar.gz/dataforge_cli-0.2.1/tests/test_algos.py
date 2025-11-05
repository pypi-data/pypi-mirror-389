import algos


def test_merge_sort_orders_by_key():
    unsorted_data = [(1, 5), (2, 2), (3, 9)]
    sorted_list = algos.merge_sort(unsorted_data, key_index=1)
    assert sorted_list == [(2, 2), (1, 5), (3, 9)]


def test_merge_sort_handles_empty_list():
    assert algos.merge_sort([], key_index=0) == []


def test_binary_search_finds_existing_value():
    sorted_list = [(1, "a"), (2, "b"), (3, "c")]
    index = algos.binary_search(sorted_list, "b", key_index=1)
    assert index == 1


def test_binary_search_returns_minus_one_when_missing():
    sorted_list = [(1, "a"), (2, "b"), (3, "c")]
    index = algos.binary_search(sorted_list, "z", key_index=1)
    assert index == -1
