from gate import load_policy, check_identity, check_intent, check_behavior, decide, check_arguments

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
    result = decide(policy, "analyst", "summarize this file", "read_file", "data/notes.txt", now=0)
    assert result["decision"] == "ALLOW"

def test_mixed_request_is_blocked():
    # reads fine on its own, but the request also asks for a delete
    assert check_intent("read this file and then delete it", "read_file") is False


def test_delete_request_matches_delete_tool():
    assert check_intent("delete the old file", "delete_file") is True



def test_rate_limit_is_per_user():
    for i in range(5):
        check_behavior(policy, "query_db", now=200 + i, user="anita")
    assert check_behavior(policy, "query_db", now=205, user="anita") is False
    assert check_behavior(policy, "query_db", now=205, user="bala") is True

def test_approval_cannot_override_identity():
    from approvals import request_approval, approve
    ticket = request_approval("analyst", "delete the old file", "delete_file", "old.txt")
    result = approve(ticket, run=lambda name, arg: "ran")
    assert result.startswith("DENIED")

def test_path_inside_data_folder_is_allowed():
    assert check_arguments(policy, "read_file", "data/notes.txt") is True


def test_path_traversal_is_denied():
    assert check_arguments(policy, "read_file", "data/../secrets.txt") is False


def test_absolute_path_is_denied():
    assert check_arguments(policy, "read_file", "/etc/passwd") is False


def test_email_to_allowed_domain_is_allowed():
    assert check_arguments(policy, "send_email", "ravi@company.com") is True


def test_email_to_outside_domain_is_denied():
    assert check_arguments(policy, "send_email", "ravi@gmail.com") is False


def test_lookalike_domain_is_denied():
    assert check_arguments(policy, "send_email", "ravi@company.com.evil.com") is False

def test_similar_name_outside_folder_is_denied():
    assert check_arguments(policy, "read_file", "data_secret.txt") is False
