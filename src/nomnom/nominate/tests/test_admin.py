import pytest
from django.contrib.auth import get_user_model
from faker import Faker

from nomnom.nominate import factories
from nomnom.nominate.admin import MemberCreationForm

UserModel = get_user_model()
fake = Faker()

pytestmark = pytest.mark.usefixtures("db")


class TestMemberCreationForm:
    """Tests for the MemberCreationForm used in admin to manually create members."""

    def test_creates_user_with_email_when_saving_new_member(self):
        """Test that creating a new member also creates a user with the correct email."""
        member_number = fake.numerify(text="######")
        preferred_name = fake.name()
        email_address = fake.email()

        form_data = {
            "member_number": member_number,
            "preferred_name": preferred_name,
            "email_address": email_address,
        }
        form = MemberCreationForm(data=form_data)

        assert form.is_valid(), f"Form errors: {form.errors}"

        member = form.save()

        # Verify member was created
        assert member.member_number == member_number
        assert member.preferred_name == preferred_name

        # Verify user was created and associated
        assert member.user is not None
        assert member.user.username == f"manual-{member_number}"

        # Verify email was set correctly
        assert member.user.email == email_address

        # Verify the user was actually saved to the database
        saved_user = UserModel.objects.get(username=f"manual-{member_number}")
        assert saved_user.email == email_address

    def test_creates_user_without_email_when_email_not_provided(self):
        """Test that creating a member without email still creates the user."""
        member_number = fake.numerify(text="######")
        preferred_name = fake.name()

        form_data = {
            "member_number": member_number,
            "preferred_name": preferred_name,
            "email_address": "",
        }
        form = MemberCreationForm(data=form_data)

        assert form.is_valid(), f"Form errors: {form.errors}"

        member = form.save()

        # Verify member and user were created
        assert member.user is not None
        assert member.user.username == f"manual-{member_number}"

        # Verify email is empty
        assert member.user.email == ""

    def test_initializes_email_field_for_existing_member(self):
        """Test that the form initializes with existing user's email."""
        # Create a user and member using factories
        existing_email = fake.email()
        user = factories.UserFactory(email=existing_email)
        user.set_unusable_password()
        user.save()

        member = factories.NominatingMemberProfileFactory(user=user)

        # Initialize form with existing instance
        form = MemberCreationForm(instance=member)

        # Verify email field is populated
        assert form.fields["email_address"].initial == existing_email

    def test_does_not_recreate_user_for_existing_member(self):
        """Test that saving an existing member doesn't create a new user."""
        # Create a user and member using factories
        old_email = fake.email()
        user = factories.UserFactory(email=old_email)
        user.set_unusable_password()
        user.save()

        member = factories.NominatingMemberProfileFactory(user=user)

        original_user_id = user.id

        # Update the member through the form
        form_data = {
            "member_number": member.member_number,
            "preferred_name": fake.name(),
            "email_address": fake.email(),  # Note: This won't update existing user
        }
        form = MemberCreationForm(data=form_data, instance=member)

        assert form.is_valid(), f"Form errors: {form.errors}"

        updated_member = form.save()

        # Verify it's still the same user
        assert updated_member.user.id == original_user_id

        # The email should NOT have changed (form only sets email on new users)
        assert updated_member.user.email == old_email

    def test_user_has_unusable_password(self):
        """Test that created users have unusable passwords."""
        member_number = fake.numerify(text="######")

        form_data = {
            "member_number": member_number,
            "preferred_name": fake.name(),
            "email_address": fake.email(),
        }
        form = MemberCreationForm(data=form_data)

        assert form.is_valid()
        member = form.save()

        # Verify password is unusable
        assert not member.user.has_usable_password()
