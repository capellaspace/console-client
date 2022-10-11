from capella_console_client.search import SearchResult

from .test_data import get_canned_search_results


def test_search_result_add_drops_dupes():
    page = get_canned_search_results()
    result = SearchResult()
    added = result.add(page)
    assert added == len(page["features"])
    orig_len = len(result)

    # all dupes -> all filtered
    added = result.add(page)
    assert added == 0
    assert orig_len == len(result)


def test_search_result_add_drops_keep_dupes():
    page = get_canned_search_results()
    result = SearchResult()
    added = result.add(page)
    assert added == len(page["features"])
    added = result.add(page, keep_duplicates=True)
    assert added == len(page["features"])
    assert len(result) == 2 * len(page["features"])


def test_search_result_merge_dupes():
    page = get_canned_search_results()
    result1 = SearchResult()
    result1.add(page)

    result2 = SearchResult()
    result1.add(page)

    orig_len1 = len(result1)
    orig_len2 = len(result2)
    merged = result1.merge(result2)

    assert len(merged) == len(result1)
    assert orig_len1 == len(result1)
    assert orig_len2 == len(result2)


def test_search_result_merge_keep():
    page = get_canned_search_results()
    result1 = SearchResult()
    result1.add(page)

    result2 = SearchResult()
    result1.add(page)

    orig_len1 = len(result1)
    orig_len2 = len(result2)
    merged = result1.merge(result2, keep_duplicates=True)

    assert len(merged) == len(result1) + len(result2)
    assert orig_len1 == len(result1)
    assert orig_len2 == len(result2)
