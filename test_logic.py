"""
Unit verification script for NeighborTools logic and fallbacks.
"""

from datetime import date, timedelta
import database

def run_tests():
    print("--- Running Test 1: Sign up in preview mode ---")
    # Temporarily force get_client to return None for mock mode testing
    orig_get_client = database.get_client
    database.get_client = lambda access_token=None: None

    success, msg, user_data, token = database.sign_up_user("testuser@example.com", "password123", "Test User", "Downtown")
    assert success is True, "Sign up should succeed in preview mode"
    assert user_data is not None, "user_data must be returned"
    assert token == "mock_token", "access_token must be mock_token in preview mode"
    print("Test 1 Passed: sign_up_user returns valid session token in preview mode.")

    print("--- Running Test 2: Sign in in preview mode ---")
    success, msg, user_data, token = database.sign_in_user("testuser@example.com", "password123")
    assert success is True, "Sign in should succeed"
    assert token == "mock_token", "access_token must be mock_token"
    print("Test 2 Passed: sign_in_user works cleanly.")

    print("--- Running Test 3: Concurrency / Overlap prevention in reservations ---")
    today = date.today()
    d1 = today + timedelta(days=10)
    d2 = today + timedelta(days=15)
    d3 = today + timedelta(days=12)
    d4 = today + timedelta(days=18)

    # Reset mock reservations
    database.MOCK_RESERVATIONS.clear()
    
    # User 1 requests Tool 1
    res1_ok, msg1 = database.create_reservation("tool_1", "u_demo_2", d1, d2, "Fixing deck")
    assert res1_ok is True, f"Reservation 1 should succeed: {msg1}"
    r1_id = database.MOCK_RESERVATIONS[0]["id"]

    # User 2 requests Tool 1 with overlapping dates
    res2_ok, msg2 = database.create_reservation("tool_1", "u_demo_3", d3, d4, "Roof work")
    assert res2_ok is True, f"Reservation 2 should succeed as pending: {msg2}"
    r2_id = database.MOCK_RESERVATIONS[0]["id"]

    # Approve Reservation 1
    appr1_ok, appr1_msg = database.approve_reservation(r1_id, "u_demo_1")
    assert appr1_ok is True, f"Approval 1 should succeed: {appr1_msg}"
    assert database.MOCK_RESERVATIONS[1]["status"] == "approved" or database.MOCK_RESERVATIONS[0]["status"] == "approved"

    # Attempt to approve Reservation 2 (overlapping dates on same tool)
    appr2_ok, appr2_msg = database.approve_reservation(r2_id, "u_demo_1")
    assert appr2_ok is False, "Approval 2 must fail due to overlap conflict!"
    assert "overlapping" in appr2_msg.lower() or "conflict" in appr2_msg.lower(), f"Expected overlap message, got: {appr2_msg}"
    print("Test 3 Passed: Overlapping reservation approval blocked successfully.")

    print("--- Running Test 4: Handover pickup and return transitions ---")
    # Mark Reservation 1 picked up
    pick_ok, pick_msg = database.mark_handover_pickup(r1_id, "u_demo_1", "Good condition")
    assert pick_ok is True, f"Pickup should succeed: {pick_msg}"
    
    # Try invalid pickup on Reservation 2 (which is pending)
    pick_bad, _ = database.mark_handover_pickup(r2_id, "u_demo_1")
    assert pick_bad is False, "Pickup must fail on pending reservation"

    # Return Reservation 1
    ret_ok, ret_msg = database.mark_handover_return(r1_id, "u_demo_2", "Returned clean")
    assert ret_ok is True, f"Return should succeed: {ret_msg}"
    print("Test 4 Passed: Handover pickup and return validated.")

    print("--- Running Test 5: Review creation and duplicate enforcement ---")
    rev1_ok, rev1_msg = database.create_review(r1_id, "u_demo_2", "u_demo_1", 5, "Great drill!")
    assert rev1_ok is True, f"Review 1 should succeed: {rev1_msg}"

    # Try duplicate review
    rev2_ok, rev2_msg = database.create_review(r1_id, "u_demo_2", "u_demo_1", 4, "Trying again")
    assert rev2_ok is False, "Duplicate review must be rejected"
    print("Test 5 Passed: Duplicate review prevented.")

    print("--- Running Test 6: Verify RPC failure handling without direct fallback ---")
    # Restore original client
    database.get_client = orig_get_client
    
    # Create a mock client that raises an exception on rpc to simulate rpc failure or missing function
    class FailingRpc:
        def execute(self):
            raise Exception("Function approve_reservation does not exist")
    class MockClient:
        def rpc(self, name, params):
            return FailingRpc()
        def table(self, name):
            raise AssertionError("CRITICAL FAILURE: Table update fallback was invoked!")

    database.get_client = lambda access_token=None: MockClient()

    fail_ok, fail_err = database.approve_reservation("some_res_id", "some_owner_id", "some_token")
    assert fail_ok is False, "Must return failure when RPC fails"
    assert "failed to approve" in fail_err.lower(), f"Unexpected error message: {fail_err}"
    print("Test 6 Passed: approve_reservation returns clean error without invoking table update fallback.")

    print("--- Running Test 7: Verify pickup and return without table update fallback ---")
    p_ok, p_err = database.mark_handover_pickup("some_res_id", "some_owner_id", "note", "some_token")
    assert p_ok is False, "Must return failure when RPC fails"
    assert "failed to record pickup" in p_err.lower()

    r_ok, r_err = database.mark_handover_return("some_res_id", "some_owner_id", "note", "some_token")
    assert r_ok is False, "Must return failure when RPC fails"
    assert "failed to record return" in r_err.lower()
    print("Test 7 Passed: Pickup and return return clean errors without invoking table update fallback.")

    # Restore client
    database.get_client = orig_get_client

    print("\nALL 7 TESTS PASSED SUCCESSFULLY! [OK]")

if __name__ == "__main__":
    run_tests()
