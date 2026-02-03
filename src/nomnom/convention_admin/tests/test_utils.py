"""
Tests for convention_admin utility functions.
"""

from nomnom.convention_admin.utils import (
    WorkSelector,
    VariationGenerator,
    get_nomination_distribution,
    select_random_ip,
)


class TestWorkSelector:
    """Test cases for WorkSelector utility class."""

    def test_init_with_valid_works(self):
        """Test WorkSelector initialization with valid works."""
        works = [
            {"canonical": {"field_1": "Work 1"}, "popularity_weight": 10},
            {"canonical": {"field_1": "Work 2"}, "popularity_weight": 5},
        ]
        selector = WorkSelector(works)
        assert selector.works == works
        # With default threshold 6, only work 1 (weight 10) is popular
        assert len(selector.popular_works) == 1
        assert len(selector.other_works) == 1

    def test_init_with_empty_works(self):
        """Test WorkSelector initialization with empty list."""
        selector = WorkSelector([])
        assert selector.works == []
        assert len(selector.popular_works) == 0
        assert len(selector.other_works) == 0

    def test_select_work_returns_valid_work(self):
        """Test that select_work returns a valid work from the list."""
        works = [
            {"canonical": {"field_1": "Work 1"}, "popularity_weight": 10},
            {"canonical": {"field_1": "Work 2"}, "popularity_weight": 5},
            {"canonical": {"field_1": "Work 3"}, "popularity_weight": 1},
        ]
        selector = WorkSelector(works)

        # Select 100 works and ensure they're all valid
        for _ in range(100):
            work = selector.select_work()
            assert work in works

    def test_select_work_respects_weights(self):
        """Test that popular works are selected more often (probabilistic test)."""
        works = [
            {"canonical": {"field_1": "Popular"}, "popularity_weight": 100},
            {"canonical": {"field_1": "Unpopular"}, "popularity_weight": 1},
        ]
        selector = WorkSelector(works, popular_threshold=50)

        # Select 1000 works from popular works only
        selections = [selector.select_work(use_popular=True) for _ in range(1000)]
        popular_count = sum(
            1 for w in selections if w["canonical"]["field_1"] == "Popular"
        )

        # Popular work should be selected much more often (at least 95% of the time)
        # With weight 100 vs 1, this should be very reliable
        assert popular_count > 950, (
            f"Expected >950 popular selections, got {popular_count}"
        )

    def test_select_work_with_zero_weight(self):
        """Test handling of works with zero weight."""
        works = [
            {"canonical": {"field_1": "Normal"}, "popularity_weight": 10},
            {"canonical": {"field_1": "Zero Weight"}, "popularity_weight": 0},
        ]
        selector = WorkSelector(works, popular_threshold=5)

        # Select many works - zero weight work should rarely (if ever) appear
        selections = [selector.select_work(use_popular=True) for _ in range(100)]
        zero_weight_count = sum(
            1 for w in selections if w["canonical"]["field_1"] == "Zero Weight"
        )

        # With zero weight, it should basically never be selected
        # (though random.choices might select it very rarely)
        assert zero_weight_count < 10


class TestVariationGenerator:
    """Test cases for VariationGenerator utility class."""

    def test_select_variation_returns_dict(self):
        """Test that select_variation returns a dictionary."""
        work = {
            "canonical": {"field_1": "The Test Work", "field_2": "Author Name"},
            "variations": [
                {"field_1": "Test Work", "field_2": "Author Name"},
                {"field_1": "The Test", "field_2": "A. Name"},
            ],
        }
        result = VariationGenerator.select_variation(work)
        assert isinstance(result, dict)
        assert "field_1" in result

    def test_select_variation_returns_valid_option(self):
        """Test that select_variation returns either canonical or variation."""
        work = {
            "canonical": {"field_1": "The Test Work", "field_2": "Author"},
            "variations": [
                {"field_1": "Test Work", "field_2": "Author"},
                {"field_1": "The Test", "field_2": "Author"},
            ],
        }

        # Collect 100 selections
        selections = [VariationGenerator.select_variation(work) for _ in range(100)]

        # All should be valid (either canonical or one of the variations)
        valid_options = [work["canonical"]] + work["variations"]
        for selection in selections:
            assert selection in valid_options

    def test_select_variation_favors_canonical(self):
        """Test that canonical form is selected sometimes (probabilistic test)."""
        work = {
            "canonical": {"field_1": "Canonical Form", "field_2": "Author"},
            "variations": [
                {"field_1": "Variation 1", "field_2": "Author"},
                {"field_1": "Variation 2", "field_2": "Author"},
                {"field_1": "Variation 3", "field_2": "Author"},
            ],
        }

        # Select 1000 times
        selections = [VariationGenerator.select_variation(work) for _ in range(1000)]
        canonical_count = sum(1 for s in selections if s == work["canonical"])

        # Canonical should appear about 30% of the time (allow 20-40% range)
        assert 200 < canonical_count < 400, (
            f"Expected 200-400 canonical selections, got {canonical_count}"
        )

    def test_select_variation_with_no_variations(self):
        """Test select_variation when work has no variations."""
        work = {
            "canonical": {"field_1": "Only Form", "field_2": "Author"},
            "variations": [],
        }

        # Should always return canonical
        for _ in range(10):
            result = VariationGenerator.select_variation(work)
            assert result == work["canonical"]

    def test_select_variation_with_single_variation(self):
        """Test select_variation with only one variation."""
        work = {
            "canonical": {"field_1": "Canonical", "field_2": "Author"},
            "variations": [{"field_1": "Variation", "field_2": "Author"}],
        }

        # Should return either canonical or the single variation
        selections = [VariationGenerator.select_variation(work) for _ in range(100)]
        for selection in selections:
            assert selection in [work["canonical"], work["variations"][0]]


class TestGetNominationDistribution:
    """Test cases for get_nomination_distribution function."""

    def test_returns_dict_with_required_keys(self):
        """Test that function returns distribution with required keys."""
        result = get_nomination_distribution(100)

        # Check that required keys exist
        assert "major_fiction_participants" in result
        assert "other_category_participants" in result
        assert "nominations_per_participant" in result

    def test_participation_rates_are_valid(self):
        """Test that all participation rates are between 0 and total nominators."""
        total = 100
        result = get_nomination_distribution(total)

        # Major fiction participants should be 70-90% of total
        assert 70 <= result["major_fiction_participants"] <= 90

        # Other category participants should be 40-60% of total
        assert 40 <= result["other_category_participants"] <= 60

        # Nominations per participant should be 3-5
        assert 3 <= result["nominations_per_participant"] <= 5

    def test_non_fiction_categories_have_lower_participation(self):
        """Test that non-fiction categories have lower participation than fiction."""
        total = 100
        result = get_nomination_distribution(total)

        # Other category participants should be less than major fiction
        assert (
            result["other_category_participants"] < result["major_fiction_participants"]
        )


class TestSelectRandomIp:
    """Test cases for select_random_ip function."""

    def test_returns_valid_ip_format(self):
        """Test that function returns a valid IPv4 address format."""
        ip = select_random_ip()
        parts = ip.split(".")

        assert len(parts) == 4, f"IP should have 4 octets, got: {ip}"

        # All parts should be integers
        for part in parts:
            assert part.isdigit(), f"IP octet should be numeric, got: {part}"

    def test_returns_different_ips(self):
        """Test that function generates variety in IPs."""
        ips = [select_random_ip() for _ in range(100)]

        # Should generate at least some variety (not all the same)
        unique_ips = set(ips)
        assert len(unique_ips) > 50, (
            f"Expected variety in IPs, got only {len(unique_ips)} unique IPs"
        )

    def test_octets_are_in_valid_range(self):
        """Test that all octets are in valid IPv4 range (0-255)."""
        for _ in range(100):
            ip = select_random_ip()
            octets = [int(x) for x in ip.split(".")]

            for octet in octets:
                assert 0 <= octet <= 255, f"Octet {octet} out of valid range"

    def test_consistent_format(self):
        """Test that IP format is consistent across multiple calls."""
        for _ in range(50):
            ip = select_random_ip()
            # Should match IPv4 format: X.X.X.X where X is 0-255
            parts = ip.split(".")
            assert len(parts) == 4
            for part in parts:
                assert 0 <= int(part) <= 255
