import pytest

from nomnom.wsfs.rules.constitution_2023 import CountData


@pytest.fixture
def sample_eph_steps():
    """Sample EPH steps data structure for testing."""
    # Step 1: 5 works, eliminate Work_E
    step1_counts = {
        "Work A": CountData(nominations=10, ballot_count=8, points=570),
        "Work B": CountData(nominations=8, ballot_count=7, points=480),
        "Work C": CountData(nominations=7, ballot_count=6, points=420),
        "Work D": CountData(nominations=6, ballot_count=5, points=360),
        "Work E": CountData(nominations=4, ballot_count=4, points=240),
    }
    step1_eliminations = ["Work E"]

    # Step 2: 4 works, eliminate Work_D
    # Points increase as Work E's votes are redistributed
    step2_counts = {
        "Work A": CountData(nominations=10, ballot_count=8, points=600),
        "Work B": CountData(nominations=8, ballot_count=7, points=510),
        "Work C": CountData(nominations=7, ballot_count=6, points=450),
        "Work D": CountData(nominations=6, ballot_count=5, points=375),
    }
    step2_eliminations = ["Work D"]

    # Step 3: 3 works remain (finalists)
    # Points increase again as Work D's votes are redistributed
    step3_counts = {
        "Work A": CountData(nominations=10, ballot_count=8, points=660),
        "Work B": CountData(nominations=8, ballot_count=7, points=570),
        "Work C": CountData(nominations=7, ballot_count=6, points=510),
    }
    step3_eliminations = []

    return [
        ([], step1_counts, step1_eliminations),
        ([], step2_counts, step2_eliminations),
        ([], step3_counts, step3_eliminations),
    ]


def test_sample_eph_steps(sample_eph_steps):
    """Verify sample EPH steps fixture structure."""
    assert len(sample_eph_steps) == 3

    # Check step 1
    ballots, counts, eliminations = sample_eph_steps[0]
    assert len(counts) == 5
    assert eliminations == ["Work E"]
    assert "Work A" in counts
    assert counts["Work A"].points == 570

    # Check step 3 (finalists)
    ballots, counts, eliminations = sample_eph_steps[2]
    assert len(counts) == 3
    assert eliminations == []


def test_transform_basic_structure(sample_eph_steps):
    """Test basic structure of transform_eph_to_sankey output."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    # Check returned structure
    assert "nodes" in result
    assert "links" in result
    assert isinstance(result["nodes"], list)
    assert isinstance(result["links"], list)

    # Links should be present (continuation links)
    assert len(result["links"]) > 0


def test_transform_node_count_full_mode(sample_eph_steps):
    """Test node count in full mode (all steps)."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    # Step 0: 5 works, Step 1: 4 works, Step 2: 3 works = 12 work nodes
    # Plus potentially "Other" nodes for redistribution grouping

    # Count work nodes (non-Other nodes)
    work_nodes = [n for n in nodes if not n["name"].startswith("Other")]
    assert len(work_nodes) == 12

    # Verify we have at least the work nodes
    assert len(nodes) >= 12


def test_transform_node_structure(sample_eph_steps):
    """Test individual node structure and fields."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    # Check first node (Work A, Step 0)
    node = result["nodes"][0]
    assert "id" in node
    assert "name" in node
    assert "step" in node
    assert "points" in node
    assert "nominations" in node
    assert "status" in node
    assert "is_finalist" in node
    assert "first_appearance" in node

    # Verify node ID format
    assert node["id"] == "Work A_step_0"
    assert node["name"] == "Work A"
    assert node["step"] == 0
    assert node["points"] == 570
    assert node["nominations"] == 10


def test_transform_node_status(sample_eph_steps):
    """Test node status assignment (finalist, close, early)."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]

    # Find Work E at step 0 (eliminated with 240 points)
    # Step 0 finalists: Work A (570), Work B (480), Work C (420)
    # Min finalist points: 420
    # Threshold: 0.75 * 420 = 315
    # Work E points: 240 < 315, so status should be "early"
    work_e_nodes = [n for n in nodes if n["name"] == "Work E"]
    assert len(work_e_nodes) == 1
    assert work_e_nodes[0]["status"] == "early"

    # Find Work A at step 2 (finalist)
    work_a_final = [n for n in nodes if n["name"] == "Work A" and n["step"] == 2]
    assert len(work_a_final) == 1
    assert work_a_final[0]["status"] == "finalist"
    assert work_a_final[0]["is_finalist"] is True

    # Find Work D at step 1 (eliminated with 375 points)
    # Step 1 finalists: Work A (600), Work B (510), Work C (450)
    # Min finalist points: 450
    # Threshold: 0.75 * 450 = 337.5
    # Work D points: 375 > 337.5, so status should be "close"
    work_d_nodes = [n for n in nodes if n["name"] == "Work D" and n["step"] == 1]
    assert len(work_d_nodes) == 1
    assert work_d_nodes[0]["status"] == "close"


def test_transform_first_appearance_tracking(sample_eph_steps):
    """Test first_appearance field tracks when work first appeared."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]

    # All works first appear at step 0
    for node in nodes:
        if node["name"] in ["Work A", "Work B", "Work C", "Work D", "Work E"]:
            assert node["first_appearance"] == 0


def _make_extended_steps(sample_eph_steps):
    """Build extended steps with >15 candidates in early rounds so compact mode trims them.

    Creates 10 steps each with 16 dummy works (one eliminated per step), then appends
    sample_eph_steps (which have ≤5 candidates each). Compact mode's backwards scan for
    ``size >= 15`` will stop at step 9 (16 works), making steps 9-12 visible.
    """
    base_works = {
        f"Filler {j}": CountData(nominations=5, ballot_count=4, points=300)
        for j in range(16)
    }
    extended_steps = []
    remaining = dict(base_works)
    for i in range(10):
        eliminated = f"Filler {i}"
        extended_steps.append(([], dict(remaining), [eliminated]))
        del remaining[eliminated]
    extended_steps.extend(sample_eph_steps)
    return extended_steps


def test_transform_compact_mode_filters_steps(sample_eph_steps):
    """Test compact mode filters to steps from when ≤15 candidates remain."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    extended_steps = _make_extended_steps(sample_eph_steps)

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(extended_steps, finalists, mode="compact")

    nodes = result["nodes"]

    # Compact mode should trim early steps that have >15 candidates,
    # so we should get fewer nodes than full mode.
    result_full = transform_eph_to_sankey(extended_steps, finalists, mode="full")
    assert len(nodes) < len(result_full["nodes"])

    # Verify step indices are 0-based (normalized from visible window)
    for node in nodes:
        assert node["step"] >= 0


def test_transform_mode_default_is_compact(sample_eph_steps):
    """Test default mode is compact."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}

    # Call without mode parameter
    result_default = transform_eph_to_sankey(sample_eph_steps, finalists)
    result_compact = transform_eph_to_sankey(
        sample_eph_steps, finalists, mode="compact"
    )

    # Should produce same result
    assert len(result_default["nodes"]) == len(result_compact["nodes"])


def test_transform_status_threshold_edge_cases():
    """Test status threshold calculation edge cases."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    # Create a scenario with works at various point thresholds
    # Finalists: Work A (400), Work B (350), Work C (300)
    # Min finalist points: 300
    # Threshold: 0.75 * 300 = 225

    step_counts = {
        "Work A": CountData(nominations=10, ballot_count=8, points=400),
        "Work B": CountData(nominations=9, ballot_count=7, points=350),
        "Work C": CountData(nominations=8, ballot_count=6, points=300),
        # Work D exactly at threshold (225) - should be "early" (≤75%)
        "Work D": CountData(nominations=7, ballot_count=5, points=225),
        # Work E just above threshold (226) - should be "close" (>75%)
        "Work E": CountData(nominations=6, ballot_count=4, points=226),
        # Work F well below threshold (100) - should be "early"
        "Work F": CountData(nominations=5, ballot_count=3, points=100),
        # Work G close to threshold but below (224) - should be "early"
        "Work G": CountData(nominations=4, ballot_count=2, points=224),
    }

    eliminations = ["Work D", "Work E", "Work F", "Work G"]
    steps = [([], step_counts, eliminations)]
    finalists = {"Work A", "Work B", "Work C"}

    result = transform_eph_to_sankey(steps, finalists, mode="full")
    nodes = result["nodes"]

    # Check finalists - count unique finalist names (not nodes, since finalists appear in multiple steps)
    finalist_nodes = [n for n in nodes if n["is_finalist"]]
    unique_finalists = {n["name"] for n in finalist_nodes}
    assert len(unique_finalists) == 3
    for node in finalist_nodes:
        assert node["status"] == "finalist"

    # Work D: 225 points = exactly at threshold (≤75%) -> "early"
    work_d = [n for n in nodes if n["name"] == "Work D"][0]
    assert work_d["points"] == 225
    assert work_d["status"] == "early"

    # Work E: 226 points > 225 threshold -> "close"
    work_e = [n for n in nodes if n["name"] == "Work E"][0]
    assert work_e["points"] == 226
    assert work_e["status"] == "close"

    # Work F: 100 points < threshold -> "early"
    work_f = [n for n in nodes if n["name"] == "Work F"][0]
    assert work_f["points"] == 100
    assert work_f["status"] == "early"

    # Work G: 224 points < threshold -> "early"
    work_g = [n for n in nodes if n["name"] == "Work G"][0]
    assert work_g["points"] == 224
    assert work_g["status"] == "early"


def test_transform_status_threshold_changes_across_steps():
    """Test that threshold recalculates per step as finalist points change."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    # Step 1: 4 works, Work D eliminated
    # Finalists in this step: A (400), B (350), C (300)
    # Min: 300, threshold: 225
    # Work D (250) > 225 -> "close"
    step1_counts = {
        "Work A": CountData(nominations=10, ballot_count=8, points=400),
        "Work B": CountData(nominations=9, ballot_count=7, points=350),
        "Work C": CountData(nominations=8, ballot_count=6, points=300),
        "Work D": CountData(nominations=7, ballot_count=5, points=250),
    }
    step1_eliminations = ["Work D"]

    # Step 2: 3 works remain (finalists)
    # Points increase after redistribution
    # Finalists: A (500), B (450), C (400)
    # Min: 400, new threshold: 300
    # If Work D still appeared here (it doesn't), its 250 points would now be < 300 -> "early"
    step2_counts = {
        "Work A": CountData(nominations=10, ballot_count=8, points=500),
        "Work B": CountData(nominations=9, ballot_count=7, points=450),
        "Work C": CountData(nominations=8, ballot_count=6, points=400),
    }
    step2_eliminations = []

    steps = [
        ([], step1_counts, step1_eliminations),
        ([], step2_counts, step2_eliminations),
    ]
    finalists = {"Work A", "Work B", "Work C"}

    result = transform_eph_to_sankey(steps, finalists, mode="full")
    nodes = result["nodes"]

    # Work D at step 0: 250 > 225 threshold -> "close"
    work_d_step0 = [n for n in nodes if n["name"] == "Work D" and n["step"] == 0][0]
    assert work_d_step0["points"] == 250
    assert work_d_step0["status"] == "close"

    # Verify finalists at step 1
    finalists_step1 = [n for n in nodes if n["step"] == 1 and n["is_finalist"]]
    assert len(finalists_step1) == 3
    for node in finalists_step1:
        assert node["status"] == "finalist"


def test_transform_status_no_finalists_in_step():
    """Test status calculation when no finalists exist in a step (edge case)."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    # Unusual case: a step where none of the final finalists are present yet
    # This shouldn't happen in real EPH, but we should handle it gracefully
    step_counts = {
        "Work X": CountData(nominations=5, ballot_count=4, points=200),
        "Work Y": CountData(nominations=4, ballot_count=3, points=150),
    }
    eliminations = ["Work X", "Work Y"]
    steps = [([], step_counts, eliminations)]
    finalists = {"Work A", "Work B", "Work C"}  # None in this step

    result = transform_eph_to_sankey(steps, finalists, mode="full")
    nodes = result["nodes"]

    # With no finalists in step, threshold should be 0.0
    # All eliminated works should be "close" (points > 0)
    work_x = [n for n in nodes if n["name"] == "Work X"][0]
    work_y = [n for n in nodes if n["name"] == "Work Y"][0]

    assert work_x["status"] == "close"  # 200 > 0
    assert work_y["status"] == "close"  # 150 > 0


# Task 3: Continuation Links Tests


def test_continuation_links_basic_structure(sample_eph_steps):
    """Test continuation links have correct structure."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    links = result["links"]
    assert len(links) > 0

    # Check structure of first link
    link = links[0]
    assert "source" in link
    assert "target" in link
    assert "value" in link
    assert "type" in link
    assert link["type"] == "continuation"
    assert isinstance(link["source"], int)
    assert isinstance(link["target"], int)
    assert isinstance(link["value"], int)


def test_continuation_links_count_full_mode(sample_eph_steps):
    """Test correct number of continuation links in full mode."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    links = result["links"]
    continuation_links = [link for link in links if link.get("type") == "continuation"]

    # Expected links:
    # Step 0→1: Work A, Work B, Work C, Work D (4 links)
    # Step 1→2: Work A, Work B, Work C (3 links)
    # Total: 7 continuation links
    assert len(continuation_links) == 7


def test_continuation_links_indices_valid(sample_eph_steps):
    """Test continuation link indices are valid node references."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    for link in links:
        # Source and target must be valid indices
        assert 0 <= link["source"] < len(nodes)
        assert 0 <= link["target"] < len(nodes)

        # Source and target should be different nodes
        assert link["source"] != link["target"]


def test_continuation_links_connect_same_work(sample_eph_steps):
    """Test continuation links connect the same work across steps."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]
    continuation_links = [link for link in links if link.get("type") == "continuation"]

    for link in continuation_links:
        source_node = nodes[link["source"]]
        target_node = nodes[link["target"]]

        # Same work name
        assert source_node["name"] == target_node["name"]

        # Target step is one more than source step
        assert target_node["step"] == source_node["step"] + 1


def test_continuation_links_value_is_target_points(sample_eph_steps):
    """Test continuation link value equals target step's points."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]
    continuation_links = [link for link in links if link.get("type") == "continuation"]

    for link in continuation_links:
        target_node = nodes[link["target"]]
        # Link value should equal target node's points
        assert link["value"] == target_node["points"]


def test_continuation_links_specific_work(sample_eph_steps):
    """Test specific work's continuation links have correct values."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find Work A's nodes
    work_a_nodes = [n for n in nodes if n["name"] == "Work A"]
    assert len(work_a_nodes) == 3  # Appears in all 3 steps

    # Find Work A's continuation links
    work_a_links = []
    for link in links:
        source_node = nodes[link["source"]]
        if source_node["name"] == "Work A":
            work_a_links.append(link)

    # Work A should have 2 continuation links (step 0→1, step 1→2)
    assert len(work_a_links) == 2

    # First link: step 0→1, value should be 600 (Work A's points at step 1)
    link_0_1 = [
        link
        for link in work_a_links
        if nodes[link["source"]]["step"] == 0 and nodes[link["target"]]["step"] == 1
    ][0]
    assert link_0_1["value"] == 600

    # Second link: step 1→2, value should be 660 (Work A's points at step 2)
    link_1_2 = [
        link
        for link in work_a_links
        if nodes[link["source"]]["step"] == 1 and nodes[link["target"]]["step"] == 2
    ][0]
    assert link_1_2["value"] == 660


def test_continuation_links_eliminated_work(sample_eph_steps):
    """Test eliminated work has no continuation link after elimination."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]
    continuation_links = [link for link in links if link.get("type") == "continuation"]

    # Work E is eliminated at step 0, should not appear in step 1
    work_e_nodes = [n for n in nodes if n["name"] == "Work E"]
    assert len(work_e_nodes) == 1  # Only appears in step 0
    assert work_e_nodes[0]["step"] == 0

    # Work E should have no continuation links (but may have redistribution links)
    work_e_continuation_links = [
        link for link in continuation_links if nodes[link["source"]]["name"] == "Work E"
    ]
    assert len(work_e_continuation_links) == 0

    # Work D is eliminated at step 1, should have one continuation link (0→1) but not (1→2)
    work_d_nodes = [n for n in nodes if n["name"] == "Work D"]
    assert len(work_d_nodes) == 2  # Appears in steps 0 and 1

    work_d_continuation_links = [
        link for link in continuation_links if nodes[link["source"]]["name"] == "Work D"
    ]
    assert len(work_d_continuation_links) == 1  # Only 0→1 link

    # Verify the link is step 0→1
    link = work_d_continuation_links[0]
    assert nodes[link["source"]]["step"] == 0
    assert nodes[link["target"]]["step"] == 1
    assert link["value"] == 375  # Work D's points at step 1


def test_continuation_links_compact_mode(sample_eph_steps):
    """Test continuation links work correctly in compact mode."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="compact")

    nodes = result["nodes"]
    links = result["links"]
    continuation_links = [link for link in links if link.get("type") == "continuation"]

    # In compact mode with only 3 steps, all steps are visible
    # So we should get the same continuation links as full mode
    assert len(continuation_links) == 7

    # Verify all continuation links connect consecutive steps
    for link in continuation_links:
        source_node = nodes[link["source"]]
        target_node = nodes[link["target"]]
        assert target_node["step"] == source_node["step"] + 1


def test_continuation_links_extended_dataset():
    """Test continuation links with a larger dataset."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey
    from nomnom.wsfs.rules.constitution_2023 import CountData

    # Create 5 steps with works being eliminated gradually
    steps = []

    # Step 0: 6 works
    steps.append(
        (
            [],
            {
                "Work A": CountData(nominations=10, ballot_count=9, points=600),
                "Work B": CountData(nominations=9, ballot_count=8, points=550),
                "Work C": CountData(nominations=8, ballot_count=7, points=500),
                "Work D": CountData(nominations=7, ballot_count=6, points=450),
                "Work E": CountData(nominations=6, ballot_count=5, points=400),
                "Work F": CountData(nominations=5, ballot_count=4, points=350),
            },
            ["Work F"],
        )
    )

    # Step 1: 5 works (Work F eliminated)
    steps.append(
        (
            [],
            {
                "Work A": CountData(nominations=10, ballot_count=9, points=620),
                "Work B": CountData(nominations=9, ballot_count=8, points=570),
                "Work C": CountData(nominations=8, ballot_count=7, points=520),
                "Work D": CountData(nominations=7, ballot_count=6, points=470),
                "Work E": CountData(nominations=6, ballot_count=5, points=420),
            },
            ["Work E"],
        )
    )

    # Step 2: 4 works (Work E eliminated)
    steps.append(
        (
            [],
            {
                "Work A": CountData(nominations=10, ballot_count=9, points=640),
                "Work B": CountData(nominations=9, ballot_count=8, points=590),
                "Work C": CountData(nominations=8, ballot_count=7, points=540),
                "Work D": CountData(nominations=7, ballot_count=6, points=490),
            },
            ["Work D"],
        )
    )

    # Step 3: 3 works (Work D eliminated, finalists remain)
    steps.append(
        (
            [],
            {
                "Work A": CountData(nominations=10, ballot_count=9, points=660),
                "Work B": CountData(nominations=9, ballot_count=8, points=610),
                "Work C": CountData(nominations=8, ballot_count=7, points=560),
            },
            [],
        )
    )

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]
    continuation_links = [link for link in links if link.get("type") == "continuation"]

    # Expected continuation links:
    # Step 0→1: A, B, C, D, E (5 links)
    # Step 1→2: A, B, C, D (4 links)
    # Step 2→3: A, B, C (3 links)
    # Total: 12 continuation links
    assert len(continuation_links) == 12

    # Verify finalists have continuation links through all steps
    work_a_continuation_links = [
        link for link in continuation_links if nodes[link["source"]]["name"] == "Work A"
    ]
    assert len(work_a_continuation_links) == 3  # 0→1, 1→2, 2→3

    # Verify eliminated work stops getting continuation links after elimination
    work_f_continuation_links = [
        link for link in continuation_links if nodes[link["source"]]["name"] == "Work F"
    ]
    assert len(work_f_continuation_links) == 0  # Eliminated at step 0, no continuation

    work_e_continuation_links = [
        link for link in continuation_links if nodes[link["source"]]["name"] == "Work E"
    ]
    assert len(work_e_continuation_links) == 1  # 0→1 only, eliminated at step 1


# Task 5: Redistribution Links Tests


def test_redistribution_links_basic_structure(sample_eph_steps):
    """Test redistribution links have correct structure."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    links = result["links"]

    # Find redistribution links
    redistribution_links = [link for link in links if link["type"] == "redistribution"]
    assert len(redistribution_links) > 0

    # Check structure of redistribution links
    for link in redistribution_links:
        assert "source" in link
        assert "target" in link
        assert "value" in link
        assert "type" in link
        assert link["type"] == "redistribution"
        assert isinstance(link["source"], int)
        assert isinstance(link["target"], int)
        assert isinstance(link["value"], int)
        assert link["value"] > 0


def test_redistribution_links_from_eliminated_works(sample_eph_steps):
    """Test redistribution links originate from eliminated works."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find redistribution links
    redistribution_links = [link for link in links if link["type"] == "redistribution"]

    # Check that sources are eliminated works or "Other" nodes
    for link in redistribution_links:
        source_node = nodes[link["source"]]
        # Source should be either:
        # 1. An eliminated work (status "close" or "early")
        # 2. An "Other" node (status "other")
        assert source_node["status"] in ["close", "early", "other"], (
            f"Redistribution link source should be eliminated or Other node, "
            f"got status: {source_node['status']}"
        )


def test_redistribution_links_work_e_elimination(sample_eph_steps):
    """Test Work E elimination creates redistribution links."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find Work E node at step 0
    work_e_nodes = [n for n in nodes if n["name"] == "Work E" and n["step"] == 0]
    assert len(work_e_nodes) == 1
    work_e_idx = nodes.index(work_e_nodes[0])

    # Find redistribution links from Work E
    work_e_redistribution = [
        link
        for link in links
        if link["source"] == work_e_idx and link["type"] == "redistribution"
    ]

    # Work E should have redistribution links
    # (top 3 recipients + possibly "Other" node)
    assert len(work_e_redistribution) > 0


def test_redistribution_links_top_3_recipients(sample_eph_steps):
    """Test redistribution shows top 3 recipients individually."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find Work E node at step 0
    work_e_nodes = [n for n in nodes if n["name"] == "Work E" and n["step"] == 0]
    assert len(work_e_nodes) == 1
    work_e_idx = nodes.index(work_e_nodes[0])

    # Find redistribution links from Work E (excluding links to "Other" nodes)
    work_e_to_works = [
        link
        for link in links
        if (
            link["source"] == work_e_idx
            and link["type"] == "redistribution"
            and not nodes[link["target"]]["name"].startswith("Other")
        )
    ]

    # Should have at most 3 direct links to recipient works
    assert len(work_e_to_works) <= 3


def test_redistribution_links_other_node_creation(sample_eph_steps):
    """Test 'Other' node is created for remaining recipients (Fix #13)."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find Work E node
    work_e_nodes = [n for n in nodes if n["name"] == "Work E" and n["step"] == 0]
    assert len(work_e_nodes) == 1
    work_e_idx = nodes.index(work_e_nodes[0])

    # Check if there are more than 3 recipients (which would require "Other" node)
    work_e_redistribution = [
        link
        for link in links
        if link["source"] == work_e_idx and link["type"] == "redistribution"
    ]

    # If there are more than 3 total redistributions from Work E,
    # one must be to an "Other" node
    if len(work_e_redistribution) > 3:
        other_node_links = [
            link
            for link in work_e_redistribution
            if nodes[link["target"]]["name"].startswith("Other")
        ]
        assert len(other_node_links) == 1

        # Verify "Other" node properties
        other_node = nodes[other_node_links[0]["target"]]
        assert other_node["status"] == "other"
        assert other_node["step"] == 1  # Next step (same column as recipients)
        assert other_node["is_finalist"] is False
        assert other_node["name"].startswith("Other (Work E)")


def test_redistribution_links_other_node_positioning(sample_eph_steps):
    """Test 'Other' node is placed at the next step (alongside recipients)."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find any "Other" nodes
    other_nodes = [n for n in nodes if n["name"].startswith("Other")]

    if other_nodes:
        for other_node in other_nodes:
            # Parse work name from "Other (Work X)" format
            work_name = other_node["name"].replace("Other (", "").replace(")", "")

            # Find the eliminated work's node
            eliminated_node = [
                n
                for n in nodes
                if n["name"] == work_name and n["status"] in ["close", "early"]
            ]

            if eliminated_node:
                # "Other" node should be at the NEXT step after the eliminated work
                assert other_node["step"] == eliminated_node[0]["step"] + 1, (
                    f"Other node step {other_node['step']} should be one after "
                    f"eliminated work step {eliminated_node[0]['step']}"
                )

                # There should be an inbound link from the eliminated work to "Other"
                eliminated_idx = nodes.index(eliminated_node[0])
                other_idx = nodes.index(other_node)
                inbound_links = [
                    link
                    for link in links
                    if link["source"] == eliminated_idx
                    and link["target"] == other_idx
                    and link["type"] == "redistribution"
                ]
                assert len(inbound_links) == 1, (
                    f"Expected 1 inbound link from {work_name} to Other node, "
                    f"got {len(inbound_links)}"
                )


def test_redistribution_links_other_node_is_leaf(sample_eph_steps):
    """Test 'Other' node is a leaf — inbound link only, no outgoing links.

    "Other" nodes must NOT have outgoing links to recipients. If they did,
    d3-sankey's BFS depth computation would diverge from the step-based
    nodeAlign, creating empty column slots that crash the renderer.
    The eliminated work already has direct links to top recipients.
    """
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find "Other" nodes
    other_nodes = [n for n in nodes if n["name"].startswith("Other")]

    if other_nodes:
        for other_node in other_nodes:
            other_idx = nodes.index(other_node)

            # "Other" node should have NO outgoing links
            outgoing_links = [link for link in links if link["source"] == other_idx]
            assert len(outgoing_links) == 0, (
                f"Other node {other_node['id']} should be a leaf but has "
                f"{len(outgoing_links)} outgoing links"
            )


def test_redistribution_links_point_calculation(sample_eph_steps):
    """Test redistribution point calculations are reasonable."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find Work E elimination (step 0)
    # Work E had 240 points
    # These should be redistributed to remaining works

    work_e_nodes = [n for n in nodes if n["name"] == "Work E" and n["step"] == 0]
    if work_e_nodes:
        work_e_idx = nodes.index(work_e_nodes[0])

        # Sum all redistribution from Work E
        work_e_redistribution = [
            link
            for link in links
            if link["source"] == work_e_idx and link["type"] == "redistribution"
        ]

        if work_e_redistribution:
            total_redistributed = sum(link["value"] for link in work_e_redistribution)

            # Total redistributed should be positive
            assert total_redistributed > 0

            # Check that redistributed points match the gains in continuing works
            # Work E had 240 points at step 0
            # At step 1, continuing works should have gained points
            # Total gain should roughly equal total redistributed

            # Calculate total gain for works that continue from step 0 to step 1
            continuing_works = ["Work A", "Work B", "Work C", "Work D"]
            total_gain = 0
            for work_name in continuing_works:
                step0_node = [
                    n for n in nodes if n["name"] == work_name and n["step"] == 0
                ]
                step1_node = [
                    n for n in nodes if n["name"] == work_name and n["step"] == 1
                ]
                if step0_node and step1_node:
                    gain = step1_node[0]["points"] - step0_node[0]["points"]
                    total_gain += gain

            # Total redistributed should roughly match total gain
            # (within reasonable tolerance due to EPH point calculation complexity)
            assert abs(total_redistributed - total_gain) < 10


def test_redistribution_links_work_d_elimination(sample_eph_steps):
    """Test Work D elimination creates redistribution links."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find Work D node at step 1
    work_d_nodes = [n for n in nodes if n["name"] == "Work D" and n["step"] == 1]
    assert len(work_d_nodes) == 1
    work_d_idx = nodes.index(work_d_nodes[0])

    # Find redistribution links from Work D
    work_d_redistribution = [
        link
        for link in links
        if link["source"] == work_d_idx and link["type"] == "redistribution"
    ]

    # Work D should have redistribution links to finalists
    assert len(work_d_redistribution) > 0

    # All targets should be at step 2 (next step)
    for link in work_d_redistribution:
        target_node = nodes[link["target"]]
        # Target is either a finalist at step 2 or "Other" node at step 1
        if target_node["name"].startswith("Other"):
            assert target_node["step"] == 1  # Prewindow
        else:
            assert target_node["step"] == 2


def test_redistribution_links_compact_mode(sample_eph_steps):
    """Test redistribution links work in compact mode."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="compact")

    links = result["links"]

    # Find redistribution links
    redistribution_links = [link for link in links if link["type"] == "redistribution"]

    # Should have redistribution links even in compact mode
    # (with only 3 steps, all are visible, so same as full mode)
    assert len(redistribution_links) > 0


def test_redistribution_links_no_eliminations_last_step(sample_eph_steps):
    """Test no redistribution links from final step (no eliminations)."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    # Find works at final step (step 2)
    final_step_nodes = [n for n in nodes if n["step"] == 2]
    final_step_indices = [nodes.index(n) for n in final_step_nodes]

    # Find redistribution links from final step works
    final_step_redistribution = [
        link
        for link in links
        if link["source"] in final_step_indices and link["type"] == "redistribution"
    ]

    # Should have no redistribution links from final step
    # (finalists are not eliminated)
    assert len(final_step_redistribution) == 0


def test_redistribution_links_indices_valid(sample_eph_steps):
    """Test redistribution link indices are valid node references."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    links = result["links"]

    redistribution_links = [link for link in links if link["type"] == "redistribution"]

    for link in redistribution_links:
        # Source and target must be valid indices
        assert 0 <= link["source"] < len(nodes)
        assert 0 <= link["target"] < len(nodes)

        # Source and target should be different nodes
        assert link["source"] != link["target"]


def test_redistribution_and_continuation_links_coexist(sample_eph_steps):
    """Test both continuation and redistribution links exist together."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    links = result["links"]

    continuation_links = [link for link in links if link["type"] == "continuation"]
    redistribution_links = [link for link in links if link["type"] == "redistribution"]

    # Both types should exist
    assert len(continuation_links) > 0
    assert len(redistribution_links) > 0

    # Total links should equal sum of both types
    assert len(links) == len(continuation_links) + len(redistribution_links)


def test_step_values_are_zero_based_full_mode(sample_eph_steps):
    """Verify all node step values are 0-based in full mode."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    nodes = result["nodes"]
    steps = [n["step"] for n in nodes]
    assert min(steps) == 0
    # All steps should be non-negative integers
    for node in nodes:
        assert isinstance(node["step"], int)
        assert node["step"] >= 0


def test_step_values_are_zero_based_compact_mode(sample_eph_steps):
    """Verify all node step values are 0-based in compact mode."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    extended_steps = _make_extended_steps(sample_eph_steps)

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(extended_steps, finalists, mode="compact")

    nodes = result["nodes"]
    assert len(nodes) > 0

    steps = sorted(set([n["step"] for n in nodes]))
    # Steps must start from 0 and be contiguous within the visible window
    assert min(steps) == 0
    assert all(i == v for i, v in enumerate(steps)), (
        "Steps should be 0-based and contiguous in compact mode"
    )


def test_display_step_exists_on_all_nodes(sample_eph_steps):
    """Verify every node has a display_step field."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    for node in result["nodes"]:
        assert "display_step" in node, f"Node {node['id']} missing display_step"
        assert isinstance(node["display_step"], int)


def test_display_step_preserves_absolute_index_full_mode(sample_eph_steps):
    """In full mode, display_step should equal step (since first_visible_idx=0)."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(sample_eph_steps, finalists, mode="full")

    for node in result["nodes"]:
        assert node["display_step"] == node["step"], (
            f"Node {node['id']}: display_step={node['display_step']} != step={node['step']}"
        )


def test_display_step_preserves_absolute_index_compact_mode(sample_eph_steps):
    """In compact mode, display_step has absolute indices while step is 0-based."""
    from nomnom.canonicalize.sankey import transform_eph_to_sankey

    extended_steps = _make_extended_steps(sample_eph_steps)
    # 13 steps total. Backwards scan finds step 1 with size=15 (>=15).
    # visible = steps[1:] → 12 steps. first_visible_idx = 1.

    finalists = {"Work A", "Work B", "Work C"}
    result = transform_eph_to_sankey(extended_steps, finalists, mode="compact")

    nodes = result["nodes"]
    first_visible_idx = 1  # step 1 is the last step with size >= 15

    for node in nodes:
        # display_step should be the absolute step index (>= first_visible_idx)
        assert node["display_step"] >= first_visible_idx, (
            f"Node {node['id']}: display_step={node['display_step']} < {first_visible_idx}"
        )
        # step should be 0-based
        assert node["step"] >= 0
        # The relationship: step = display_step - first_visible_idx
        assert node["step"] == node["display_step"] - first_visible_idx, (
            f"Node {node['id']}: step={node['step']} != "
            f"display_step={node['display_step']} - {first_visible_idx}"
        )
