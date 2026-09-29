from app.cdc.helpers import (
    backoff_ms,
    compare_lsn,
    make_idempotency_key,
    parse_test_decoding_change,
    should_retry,
)


def test_compare_lsn_ordering():
    assert compare_lsn(None, "0/1") == -1
    assert compare_lsn("0/1", None) == 1
    assert compare_lsn("0/16B3748", "0/16B3748") == 0
    assert compare_lsn("0/16B3748", "0/16B3749") == -1
    assert compare_lsn("1/0", "0/FFFFFFFF") == 1


def test_idempotency_key_stable():
    k1 = make_idempotency_key("p1", "shop", "orders", "abc", "0/1", "c")
    k2 = make_idempotency_key("p1", "shop", "orders", "abc", "0/1", "c")
    assert k1 == k2
    assert "shop.orders" in k1
    assert k1.endswith(":c")


def test_should_retry_and_backoff():
    assert should_retry(1, 3) is True
    assert should_retry(3, 3) is False
    assert backoff_ms(0) == 200
    assert backoff_ms(1) == 400
    assert backoff_ms(10) == 5000


def test_parse_insert():
    line = (
        "table shop.orders: INSERT: id[uuid]:'11111111-1111-1111-1111-111111111111' "
        "customer_email[text]:'a@b.com' amount_cents[integer]:100 status[text]:'pending'"
    )
    parsed = parse_test_decoding_change(line)
    assert parsed is not None
    assert parsed.op == "c"
    assert parsed.schema == "shop"
    assert parsed.table == "orders"
    assert parsed.values["customer_email"] == "a@b.com"
    assert parsed.values["amount_cents"] == 100


def test_parse_delete_and_update():
    d = parse_test_decoding_change(
        "table shop.orders: DELETE: id[uuid]:'11111111-1111-1111-1111-111111111111'"
    )
    assert d and d.op == "d"
    u = parse_test_decoding_change(
        "table shop.orders: UPDATE: id[uuid]:'11111111-1111-1111-1111-111111111111' "
        "status[text]:'paid' amount_cents[integer]:200"
    )
    assert u and u.op == "u"
    assert u.values["status"] == "paid"
