import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone

from nomnom.hugopacket.models import (
    DistributionCode,
    ElectionPacket,
    PacketFile,
    PacketItemAccess,
    PacketSection,
)
from nomnom.nominate.models import (
    Category,
    Election,
    NominatingMemberProfile,
)

User = get_user_model()


@pytest.fixture
def election(db):
    """Create a test election in voting state."""
    election = Election.objects.create(
        slug="test-2025",
        name="Test Hugo Awards 2025",
    )
    # Set election to voting state so users can access packets
    election.state = Election.STATE.VOTING
    election.save()
    return election


@pytest.fixture
def user(db):
    """Create a test user with vote permission."""
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )
    # Grant vote permission
    vote_perm = Permission.objects.get(
        codename="vote",
        content_type__app_label="nominate",
    )
    user.user_permissions.add(vote_perm)
    return user


@pytest.fixture
def member(db, user):
    """Create a test member profile."""
    return NominatingMemberProfile.objects.create(
        user=user,
        preferred_name="Test User",
    )


@pytest.fixture
def packet(db, election):
    """Create a test packet."""
    return ElectionPacket.objects.create(
        election=election,
        name="Test Packet 2025",
        s3_bucket_name="test-bucket",
        enabled=True,
    )


@pytest.fixture
def category(db, election):
    """Create a test category."""
    return Category.objects.create(
        election=election,
        name="Best Novel",
        description="Test category",
        field_1_description="Title",
        ballot_position=0,
    )


@pytest.mark.django_db
class TestPacketSection:
    """Tests for PacketSection model."""

    def test_create_section(self, packet):
        """Test creating a section."""
        section = PacketSection.objects.create(
            packet=packet,
            name="Best Novel",
            description="Top level category",
            position=0,
        )

        assert section.name == "Best Novel"
        assert section.depth == 0
        assert section.full_path == "Best Novel"

    def test_nested_sections(self, packet):
        """Test creating nested sections."""
        parent = PacketSection.objects.create(
            packet=packet,
            name="Best Novel",
            position=0,
        )

        child = PacketSection.objects.create(
            packet=packet,
            parent=parent,
            name="Author Name",
            position=0,
        )

        grandchild = PacketSection.objects.create(
            packet=packet,
            parent=child,
            name="Downloads",
            position=0,
        )

        assert parent.depth == 0
        assert child.depth == 1
        assert grandchild.depth == 2
        assert grandchild.full_path == "Best Novel / Author Name / Downloads"


@pytest.mark.django_db
class TestPacketFile:
    """Tests for PacketFile model."""

    def test_create_download_file(self, packet):
        """Test creating a download-type packet file."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Test File",
            access_type=PacketFile.AccessType.DOWNLOAD,
            s3_object_key="test/file.pdf",
            position=0,
        )

        assert file.name == "Test File"
        assert file.access_type == PacketFile.AccessType.DOWNLOAD
        assert file.available

    def test_create_code_file(self, packet):
        """Test creating a code-type packet file."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",  # Not used for CODE type
            position=0,
        )

        assert file.access_type == PacketFile.AccessType.CODE

    def test_format_code_with_template(self, packet):
        """Test formatting a code with a template."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            code_display_format="###-#####-###-####",
            position=0,
        )

        # Test with a clean alphanumeric code
        formatted = file.format_code("ABC12345DEF6789")
        assert formatted == "ABC-12345-DEF-6789"

    def test_format_code_with_mixed_case(self, packet):
        """Test formatting preserves case."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            code_display_format="###-###-###",
            position=0,
        )

        formatted = file.format_code("AbC123XyZ")
        assert formatted == "AbC-123-XyZ"

    def test_format_code_strips_non_alnum(self, packet):
        """Test that formatting strips non-alphanumeric chars from input."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            code_display_format="###-###-###",
            position=0,
        )

        # Input has dashes, should be stripped and reformatted
        formatted = file.format_code("ABC-123-XYZ")
        assert formatted == "ABC-123-XYZ"

    def test_format_code_no_template(self, packet):
        """Test that code without template is returned as-is."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            code_display_format="",
            position=0,
        )

        code = "ABC12345DEF6789"
        formatted = file.format_code(code)
        assert formatted == code

    def test_format_code_shorter_than_template(self, packet):
        """Test formatting when code is shorter than template."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            code_display_format="###-###-###-###",
            position=0,
        )

        # Only 6 characters, template expects 12
        formatted = file.format_code("ABC123")
        assert formatted == "ABC-123"

    def test_format_code_longer_than_template(self, packet):
        """Test formatting when code is longer than template."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            code_display_format="###-###",
            position=0,
        )

        # 9 characters, template only has 6 slots
        formatted = file.format_code("ABCDEFGHI")
        # Should only format the first 6, extra chars are appended directly
        assert formatted == "ABC-DEFGHI"

    def test_file_with_section(self, packet):
        """Test associating file with section."""
        section = PacketSection.objects.create(
            packet=packet,
            name="Best Novel",
            position=0,
        )

        file = PacketFile.objects.create(
            packet=packet,
            section=section,
            name="Novel PDF",
            access_type=PacketFile.AccessType.DOWNLOAD,
            s3_object_key="novels/novel.pdf",
            position=0,
        )

        assert file.section == section
        assert file in section.files.all()


@pytest.mark.django_db
class TestPacketItemAccess:
    """Tests for PacketItemAccess model."""

    def test_create_access_record(self, packet, member):
        """Test creating an access record."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Test File",
            access_type=PacketFile.AccessType.DOWNLOAD,
            s3_object_key="test/file.pdf",
            position=0,
        )

        access = PacketItemAccess.objects.create(
            packet_file=file,
            member=member,
        )

        assert access.access_count == 0
        assert access.member == member
        assert access.packet_file == file

    def test_increment_access(self, packet, member):
        """Test incrementing access count."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Test File",
            access_type=PacketFile.AccessType.DOWNLOAD,
            s3_object_key="test/file.pdf",
            position=0,
        )

        access = PacketItemAccess.objects.create(
            packet_file=file,
            member=member,
        )

        initial_time = access.last_accessed_at
        access.increment_access()

        assert access.access_count == 1
        assert access.last_accessed_at > initial_time

    def test_unique_constraint(self, packet, member):
        """Test that only one access record per member per file is allowed."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Test File",
            access_type=PacketFile.AccessType.DOWNLOAD,
            s3_object_key="test/file.pdf",
            position=0,
        )

        PacketItemAccess.objects.create(
            packet_file=file,
            member=member,
        )

        # This should raise an IntegrityError due to unique constraint
        with pytest.raises(Exception):
            PacketItemAccess.objects.create(
                packet_file=file,
                member=member,
            )


@pytest.mark.django_db
class TestDistributionCode:
    """Tests for DistributionCode model."""

    def test_create_code(self, packet):
        """Test creating a distribution code."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            position=0,
        )

        code = DistributionCode.objects.create(
            packet_file=file,
            code="ABCD-1234-EFGH-5678",
        )

        assert code.code == "ABCD-1234-EFGH-5678"
        assert code.packet_file == file
        assert code.member is None  # Not assigned yet

    def test_assign_code(self, packet, member):
        """Test assigning a code to a member."""
        file = PacketFile.objects.create(
            packet=packet,
            name="Game Download",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            position=0,
        )

        code = DistributionCode.objects.create(
            packet_file=file,
            code="ABCD-1234-EFGH-5678",
        )

        access = PacketItemAccess.objects.create(
            packet_file=file,
            member=member,
            distribution_code=code,
        )

        code.assigned_at = timezone.now()
        code.save()

        # Test relationship
        assert code.member == member
        assert access.distribution_code == code


@pytest.mark.django_db
class TestPacketViews:
    """Tests for packet views."""

    def test_index_view_requires_login(self, client, election):
        """Test that index view requires login."""
        url = reverse(
            "hugopacket:election_packet", kwargs={"election_id": election.slug}
        )
        response = client.get(url)

        # Should redirect to login
        assert response.status_code == 302
        assert "login" in response.url

    def test_index_view_with_sections(self, client, user, member, packet):
        """Test index view displays sections."""
        client.force_login(user)

        # Create section hierarchy
        section = PacketSection.objects.create(
            packet=packet,
            name="Best Novel",
            position=0,
        )

        subsection = PacketSection.objects.create(
            packet=packet,
            parent=section,
            name="Finalist Name",
            position=0,
        )

        # Create file in subsection
        PacketFile.objects.create(
            packet=packet,
            section=subsection,
            name="Novel PDF",
            access_type=PacketFile.AccessType.DOWNLOAD,
            s3_object_key="novels/novel.pdf",
            position=0,
        )

        url = reverse(
            "hugopacket:election_packet", kwargs={"election_id": packet.election.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "Best Novel" in str(response.content)
        assert "Finalist Name" in str(response.content)

    def test_download_code_assignment(self, client, user, member, packet):
        """Test that accessing a code file assigns a code."""
        client.force_login(user)

        file = PacketFile.objects.create(
            packet=packet,
            name="Game Code",
            access_type=PacketFile.AccessType.CODE,
            s3_object_key="",
            position=0,
        )

        # Create a code pool
        code = DistributionCode.objects.create(
            packet_file=file,
            code="TEST-CODE-1234",
        )

        url = reverse(
            "hugopacket:download_packet",
            kwargs={"election_id": packet.election.slug, "packet_file_id": file.id},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "TEST-CODE-1234" in str(response.content)

        # Verify code was assigned
        code.refresh_from_db()
        assert code.assigned_at is not None

        # Verify access record was created
        access = PacketItemAccess.objects.get(packet_file=file, member=member)
        assert access.distribution_code == code
        assert access.access_count == 1


@pytest.mark.django_db
class TestAdminActions:
    """Tests for admin actions."""

    def test_create_sections_from_categories(self, packet, category):
        """Test admin action to create sections from categories."""
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        from nomnom.hugopacket.admin import ElectionPacketAdmin

        admin = ElectionPacketAdmin(ElectionPacket, AdminSite())

        # Create a proper request with messages middleware
        factory = RequestFactory()
        request = factory.get("/admin/")
        request.session = {}
        request._messages = FallbackStorage(request)

        # Run the action
        admin.create_sections_from_categories(request, ElectionPacket.objects.all())

        # Verify section was created
        section = PacketSection.objects.get(packet=packet, name="Best Novel")
        assert section.position == 0
        assert section.parent is None

    def test_bulk_assign_section_action(self, packet):
        """Test bulk assigning section to packet files."""
        # Create sections
        section1 = PacketSection.objects.create(
            packet=packet, name="Section 1", position=0
        )

        # Create packet files without sections
        file1 = PacketFile.objects.create(name="File 1", packet=packet, position=0)
        file2 = PacketFile.objects.create(name="File 2", packet=packet, position=1)

        assert file1.section is None
        assert file2.section is None

        # Bulk update the files to the section
        queryset = PacketFile.objects.filter(id__in=[file1.id, file2.id])
        count = queryset.update(section=section1)

        assert count == 2

        # Verify files were updated
        file1.refresh_from_db()
        file2.refresh_from_db()

        assert file1.section == section1
        assert file2.section == section1
