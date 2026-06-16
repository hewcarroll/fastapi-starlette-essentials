from fastapi_starlette_essentials import PaginatedResponse, PaginationParams


def test_offset_and_limit():
    p = PaginationParams(page=3, page_size=20)
    assert p.offset == 40
    assert p.limit == 20


def test_create_computes_pages_and_flags():
    params = PaginationParams(page=2, page_size=10)
    resp = PaginatedResponse.create(items=[1, 2, 3], total=25, params=params)
    assert resp.total_pages == 3
    assert resp.has_next is True
    assert resp.has_prev is True
    assert resp.page == 2


def test_first_and_last_page_flags():
    first = PaginatedResponse.create(items=[1], total=5, params=PaginationParams(page=1, page_size=10))
    assert first.has_prev is False
    assert first.has_next is False  # total fits on one page