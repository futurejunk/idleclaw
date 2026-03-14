"""Tests for content filtering: inbound blocklist and outbound filtering."""

from server.src.services.content_filter import ContentFilter


INBOUND = [r"<script[\s>]", r"javascript:", r"data:text/html"]
OUTBOUND = [r"<script[\s>]", r"javascript:", r"data:text/html"]


class TestCheckInbound:
    def test_clean_prompt_allowed(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        result = cf.check_inbound([{"role": "user", "content": "What is the weather?"}])
        assert not result.blocked

    def test_script_tag_blocked(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        result = cf.check_inbound([{"role": "user", "content": "Hello <script>alert(1)</script>"}])
        assert result.blocked

    def test_javascript_uri_blocked(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        result = cf.check_inbound([{"role": "user", "content": "Visit javascript:alert(1)"}])
        assert result.blocked

    def test_data_uri_blocked(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        result = cf.check_inbound([{"role": "user", "content": "See data:text/html,<h1>hi</h1>"}])
        assert result.blocked

    def test_multiple_messages_checks_all(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "user", "content": "<script>alert(1)</script>"},
        ]
        assert cf.check_inbound(messages).blocked

    def test_case_insensitive(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        result = cf.check_inbound([{"role": "user", "content": "<SCRIPT>alert(1)</SCRIPT>"}])
        assert result.blocked

    def test_blocked_result_has_reason(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        result = cf.check_inbound([{"role": "user", "content": "<script>alert(1)</script>"}])
        assert result.reason == "regex"


class TestFilterOutbound:
    def test_clean_response_unchanged(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        assert cf.filter_outbound("The answer is 42") == "The answer is 42"

    def test_script_tag_replaced(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        result = cf.filter_outbound("Hello <script>alert(1)</script>")
        assert "[content filtered]" in result
        assert "<script>" not in result

    def test_javascript_uri_replaced(self):
        cf = ContentFilter(INBOUND, OUTBOUND)
        result = cf.filter_outbound("Visit javascript:void(0)")
        assert "[content filtered]" in result

    def test_empty_patterns(self):
        cf = ContentFilter([], [])
        assert not cf.check_inbound([{"role": "user", "content": "<script>"}]).blocked
        assert cf.filter_outbound("<script>alert(1)") == "<script>alert(1)"
