"""
Utility functions for seeding Hugo Awards data.
"""

import random


class WorkSelector:
    """
    Selects works for nominations with realistic distribution patterns.

    Uses a weighted random selection to simulate real-world voting patterns
    where certain works are more popular than others.
    """

    def __init__(self, works: list[dict], popular_threshold: int = 6):
        """
        Initialize the work selector.

        Args:
            works: List of work dictionaries with 'canonical', 'variations', and 'popularity_weight'
            popular_threshold: Popularity weight threshold for "popular" works (default: 6)
        """
        self.works = works
        self.popular_threshold = popular_threshold

        # Separate popular and less popular works
        self.popular_works = [
            w for w in works if w.get("popularity_weight", 0) >= popular_threshold
        ]
        self.other_works = [
            w for w in works if w.get("popularity_weight", 0) < popular_threshold
        ]

    def select_work(self, use_popular: bool = True) -> dict:
        """
        Select a work based on popularity weights.

        Args:
            use_popular: If True, select from popular works; otherwise from all works

        Returns:
            A work dictionary with 'canonical' and 'variations'
        """
        if use_popular and self.popular_works:
            # Weighted selection from popular works
            weights = [w.get("popularity_weight", 1) for w in self.popular_works]
            return random.choices(self.popular_works, weights=weights, k=1)[0]
        else:
            # Select from other works or all works
            pool = self.other_works if self.other_works else self.works
            if pool:
                weights = [w.get("popularity_weight", 1) for w in pool]
                return random.choices(pool, weights=weights, k=1)[0]
            return random.choice(self.works)

    def select_works_for_member(self, count: int = 5) -> list[dict]:
        """
        Select multiple works for a single member's nominations.

        Distribution:
        - 60-70% chance each work comes from popular works
        - Remaining from less popular works

        Args:
            count: Number of works to select (default: 5)

        Returns:
            List of work dictionaries
        """
        selected_works = []
        for _ in range(count):
            use_popular = random.random() < 0.65  # 65% chance of popular work
            work = self.select_work(use_popular=use_popular)
            selected_works.append(work)
        return selected_works


class VariationGenerator:
    """
    Generates realistic variations of work nominations.

    Applies various transformation types to simulate how different people
    might enter the same work with slight differences.
    """

    @staticmethod
    def select_variation(work: dict, include_canonical: bool = True) -> dict:
        """
        Select either the canonical form or a variation.

        Args:
            work: Work dictionary with 'canonical' and 'variations'
            include_canonical: If True, canonical form might be selected

        Returns:
            Dictionary with field_1, field_2, field_3 values
        """
        variations = work.get("variations", [])
        canonical = work.get("canonical", {})

        if not variations:
            return canonical

        # 30% chance of canonical form if included, otherwise always use variations
        if include_canonical and random.random() < 0.3:
            return canonical

        return random.choice(variations)

    @staticmethod
    def get_nomination_fields(work: dict, category_fields: int = 2) -> dict:
        """
        Get nomination field values for a work.

        Args:
            work: Work dictionary with 'canonical' and 'variations'
            category_fields: Number of fields the category uses (1, 2, or 3)

        Returns:
            Dictionary with field_1, field_2, field_3 keys
        """
        selected = VariationGenerator.select_variation(work)

        # Ensure we have all three fields, defaulting empty string
        return {
            "field_1": selected.get("field_1", ""),
            "field_2": selected.get("field_2", "") if category_fields >= 2 else "",
            "field_3": selected.get("field_3", "") if category_fields >= 3 else "",
        }


def get_nomination_distribution(total_nominators: int) -> dict[str, int]:
    """
    Calculate how many nominations to create per category.

    Not all members nominate in all categories. This simulates realistic
    participation rates.

    Args:
        total_nominators: Total number of nominating members

    Returns:
        Dictionary with participation statistics
    """
    # Typical participation rates:
    # - 70-90% nominate in major fiction categories
    # - 40-60% nominate in other categories
    # - Each member nominates 3-5 works per category they participate in

    major_fiction_rate = random.uniform(0.70, 0.90)
    other_category_rate = random.uniform(0.40, 0.60)

    return {
        "major_fiction_participants": int(total_nominators * major_fiction_rate),
        "other_category_participants": int(total_nominators * other_category_rate),
        "nominations_per_participant": random.randint(3, 5),
    }


def select_random_ip() -> str:
    """Generate a random IPv4 address for nomination records."""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
