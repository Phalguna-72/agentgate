from gate import load_policy, check_identity, check_intent, check_behavior, decide

policy = load_policy()


def test_analyst_can_read():
    assert check_identity(policy, "analyst", "read_file") is True


def test_analyst_cannot_delete():
    assert check_identity(policy, "analyst", "delete_file") is False


def test_unknown_role_is_denied():
    assert check_identity(policy, "intruder", "read_file") is False


def test_intent_matches_request():
    assert check_intent("please summarize this file", "read_file") is True


def test_intent_mismatch_is_blocked():
    assert check_intent("please summarize this file", "delete_file") is False


def test_behavior_blocks_sixth_call():
    results = [check_behavior(policy, "query_db", now=100 + i) for i in range(6)]
    assert results == [True, True, True, True, True, False]


def test_behavior_allows_after_window():
    # after 10 seconds, old calls no longer count
    assert check_behavior(policy, "query_db", now=1000) is True


def test_decide_denies_unauthorized_role():
    result = decide(policy, "analyst", "delete the file", "delete_file", now=0)
    assert result["decision"] == "DENY"


def test_decide_allows_valid_call():
    result = decide(policy, "analyst", "summarize this file", "read_file", now=0)
    assert result["decision"] == "ALLOW"


def test_mixed_request_is_blocked():
    # reads fine on its own, but the request also asks for a delete
    assert check_intent("read this file and then delete it", "read_file") is False


def test_delete_request_matches_delete_tool():
    assert check_intent("delete the old file", "delete_file") is True