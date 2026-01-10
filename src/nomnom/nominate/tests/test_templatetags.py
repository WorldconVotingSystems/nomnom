import pytest
from django.contrib.auth import get_user_model

from nomnom.nominate import factories
from nomnom.nominate.templatetags.nomnom_filters import (
    get_item,
    html_text,
    place,
    user_display_name,
)

User = get_user_model()


class TestStripHtmlTags:
    """Tests for the strip_html_tags filter (html_text function)."""

    def test_strips_simple_html_tags(self):
        html = "<p>Hello World</p>"
        result = html_text(html)
        assert result == "Hello World"

    def test_strips_multiple_tags(self):
        html = "<div><p>Hello</p><span>World</span></div>"
        result = html_text(html)
        assert result == "Hello World"

    def test_strips_nested_tags(self):
        html = "<div><p><strong>Bold</strong> text</p></div>"
        result = html_text(html)
        assert result == "Bold text"

    def test_handles_empty_string(self):
        assert html_text("") == ""

    def test_handles_none(self):
        # Note: The function signature requires str, but template filters
        # often receive None values in practice
        assert html_text(None) == ""  # type: ignore[arg-type]

    def test_preserves_text_without_tags(self):
        text = "Plain text"
        assert html_text(text) == text

    def test_strips_tags_with_attributes(self):
        html = '<p class="test" id="para">Text</p>'
        result = html_text(html)
        assert result == "Text"

    def test_handles_self_closing_tags(self):
        html = "<p>Line 1<br/>Line 2</p>"
        result = html_text(html)
        assert result == "Line 1 Line 2"

    def test_handles_whitespace(self):
        html = "<p>  Multiple   spaces  </p>"
        result = html_text(html)
        assert result == "Multiple   spaces"


class TestGetItem:
    """Tests for the get_item filter."""

    def test_gets_existing_key(self):
        dictionary = {"key": "value"}
        assert get_item(dictionary, "key") == "value"

    def test_returns_none_for_missing_key(self):
        dictionary = {"key": "value"}
        assert get_item(dictionary, "missing") is None

    def test_handles_empty_dict(self):
        assert get_item({}, "key") is None

    def test_handles_numeric_keys(self):
        dictionary = {1: "one", 2: "two"}
        assert get_item(dictionary, 1) == "one"

    def test_handles_nested_values(self):
        dictionary = {"outer": {"inner": "value"}}
        result = get_item(dictionary, "outer")
        assert result == {"inner": "value"}


@pytest.mark.django_db
class TestUserDisplayName:
    """Tests for the user_display_name filter.

    The filter attempts to access user.profile.display_name, but the actual
    related_name on the NominatingMemberProfile model is 'convention_profile'.
    These tests expose this bug by asserting specific expected values.
    """

    @pytest.fixture
    def user_without_profile(self):
        """User with no associated profile."""
        return factories.UserFactory.create(
            email="noprofile@example.com", first_name="John", last_name="Doe"
        )

    @pytest.fixture
    def user_with_preferred_name(self):
        """User with profile that has a preferred_name set."""
        user = factories.UserFactory.create(
            email="preferred@example.com", first_name="Jane", last_name="Smith"
        )
        factories.NominatingMemberProfileFactory.create(
            user=user, preferred_name="Preferred Display Name"
        )
        return user

    @pytest.fixture
    def user_with_empty_preferred_name(self):
        """User with profile but preferred_name is empty string."""
        user = factories.UserFactory.create(
            email="empty@example.com", first_name="FirstName", last_name="LastName"
        )
        factories.NominatingMemberProfileFactory.create(user=user, preferred_name="")
        return user

    @pytest.fixture
    def user_with_whitespace_preferred_name(self):
        """User with profile but preferred_name is only whitespace."""
        user = factories.UserFactory.create(
            email="whitespace@example.com",
            first_name="WhitespaceName",
            last_name="User",
        )
        factories.NominatingMemberProfileFactory.create(user=user, preferred_name="   ")
        return user

    @pytest.fixture
    def user_with_none_preferred_name(self):
        """User with profile but preferred_name is None."""
        user = factories.UserFactory.create(
            email="null@example.com", first_name="NullName", last_name="User"
        )
        factories.NominatingMemberProfileFactory.create(user=user, preferred_name=None)
        return user

    @pytest.fixture
    def user_without_first_name(self):
        """User with profile but no first_name set."""
        user = factories.UserFactory.create(
            email="nofirstname@example.com", first_name="", last_name="LastName"
        )
        factories.NominatingMemberProfileFactory.create(user=user, preferred_name="")
        return user

    def test_returns_preferred_name_when_set(self, user_with_preferred_name):
        """Should return preferred_name from profile.display_name."""
        result = user_display_name(user_with_preferred_name)
        # This test will FAIL because the filter looks for user.profile
        # but the model uses related_name="convention_profile"
        assert result == "Preferred Display Name", (
            f"Expected preferred name, got {result!r}. "
            "Filter may be catching AttributeError and falling back to email."
        )

    def test_returns_first_name_when_preferred_name_empty(
        self, user_with_empty_preferred_name
    ):
        """Should return first_name when preferred_name is empty.

        According to NominatingMemberProfile.display_name property:
        - Returns preferred_name if it exists and is not just whitespace
        - Otherwise returns user.first_name
        """
        result = user_display_name(user_with_empty_preferred_name)
        assert result == "FirstName", (
            f"Expected first name, got {result!r}. "
            "When preferred_name is empty, display_name should return first_name."
        )

    def test_returns_first_name_when_preferred_name_whitespace(
        self, user_with_whitespace_preferred_name
    ):
        """Should return first_name when preferred_name is only whitespace.

        The display_name property uses .strip() to check for empty strings.
        """
        result = user_display_name(user_with_whitespace_preferred_name)
        assert result == "WhitespaceName", (
            f"Expected first name, got {result!r}. "
            "Whitespace-only preferred_name should fall back to first_name."
        )

    def test_returns_first_name_when_preferred_name_none(
        self, user_with_none_preferred_name
    ):
        """Should return first_name when preferred_name is None."""
        result = user_display_name(user_with_none_preferred_name)
        assert result == "NullName", (
            f"Expected first name, got {result!r}. "
            "None preferred_name should fall back to first_name."
        )

    def test_returns_email_when_no_profile_exists(self, user_without_profile):
        """Should return email when user has no profile at all.

        This is the intended fallback behavior when profile doesn't exist.
        """
        result = user_display_name(user_without_profile)
        assert result == "noprofile@example.com", (
            f"Expected email as fallback, got {result!r}"
        )

    def test_returns_email_when_first_name_also_empty(self, user_without_first_name):
        """Should return email when both preferred_name and first_name are empty.

        This tests the ultimate fallback: when display_name returns empty string,
        the filter should return email.
        """
        result = user_display_name(user_without_first_name)
        # The filter has: return user.profile.display_name or user.email
        # So if display_name is empty, it should return email
        # BUT since user.profile doesn't exist, it will catch exception and return email
        assert result == "nofirstname@example.com", (
            f"Expected email as ultimate fallback, got {result!r}"
        )

    def test_proper_precedence_preferred_over_first_over_email(
        self, user_with_preferred_name
    ):
        """Verifies the proper precedence: preferred_name > first_name > email."""
        # This user has all three: preferred_name, first_name, and email
        user = user_with_preferred_name

        # Should return preferred name (highest priority)
        result = user_display_name(user)
        assert result == "Preferred Display Name", (
            "Should prefer preferred_name over first_name and email"
        )

        # Not testing the fallback chain here since we can't easily
        # modify the profile once created, but other tests cover those cases


class TestPlace:
    """Tests for the place filter."""

    def test_first_place(self):
        assert place(1) == "1st Place"

    def test_second_place(self):
        assert place(2) == "2nd Place"

    def test_third_place(self):
        assert place(3) == "3rd Place"

    def test_fourth_place(self):
        assert place(4) == "4th Place"

    def test_tenth_place(self):
        assert place(10) == "10th Place"

    def test_eleventh_place(self):
        assert place(11) == "11th Place"

    def test_twelfth_place(self):
        assert place(12) == "12th Place"

    def test_thirteenth_place(self):
        assert place(13) == "13th Place"

    def test_twenty_first_place(self):
        assert place(21) == "21st Place"

    def test_twenty_second_place(self):
        assert place(22) == "22nd Place"

    def test_twenty_third_place(self):
        assert place(23) == "23rd Place"

    def test_twenty_fourth_place(self):
        assert place(24) == "24th Place"

    def test_thirty_first_place(self):
        assert place(31) == "31st Place"

    def test_thirty_second_place(self):
        assert place(32) == "32nd Place"

    def test_thirty_third_place(self):
        assert place(33) == "33rd Place"

    def test_hundredth_place(self):
        assert place(100) == "100th Place"

    def test_hundred_first_place(self):
        assert place(101) == "101st Place"
