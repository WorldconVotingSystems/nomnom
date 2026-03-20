"""Transform EPH elimination steps into Sankey diagram data for d3-sankey visualization."""

from typing import Literal, TypedDict

from nomnom.wsfs.rules.constitution_2023 import CountData


class SankeyNode(TypedDict):
    id: str
    name: str
    step: int
    display_step: int
    points: float
    nominations: int
    ballot_count: int
    status: Literal["finalist", "close", "early", "active", "other"]
    is_finalist: bool
    first_appearance: int


class SankeyLink(TypedDict):
    source: int
    target: int
    value: float
    type: Literal["continuation", "redistribution"]


class SankeyData(TypedDict):
    nodes: list[SankeyNode]
    links: list[SankeyLink]


# Type alias for a single EPH step tuple
type EphStep = tuple[list, dict[str, CountData], list[str]]


def _compute_first_appearances(steps: list[EphStep]) -> dict[str, int]:
    """Compute the first step index at which each work appears.

    This must run over ALL steps before any mode filtering, so that compact mode
    preserves the correct first_appearance values.
    """
    first_appearance: dict[str, int] = {}
    for step_idx, (_ballots, counts, _eliminations) in enumerate(steps):
        for work_name in counts:
            if work_name not in first_appearance:
                first_appearance[work_name] = step_idx
    return first_appearance


def _select_visible_steps(steps: list[EphStep], mode: str) -> tuple[list[EphStep], int]:
    """Return the visible steps and the absolute index of the first visible step."""
    if mode == "compact":
        visible = steps[-10:]
        first_visible_idx = max(0, len(steps) - 10)
    else:
        visible = steps
        first_visible_idx = 0
    return visible, first_visible_idx


def _classify_elimination_status(
    work_name: str,
    count_data: CountData,
    eliminations: list[str],
    finalists: set[str],
    close_to_advance_threshold: float,
) -> Literal["finalist", "close", "early", "active", "other"]:
    """Determine the display status for a work at a given step."""
    if work_name in finalists:
        return "finalist"
    if work_name in eliminations:
        return "close" if count_data.points > close_to_advance_threshold else "early"
    return "active"


def _compute_close_to_advance_threshold(
    counts: dict[str, CountData], finalists: set[str]
) -> float:
    """Compute the 75%-of-minimum-finalist-points threshold for a step."""
    finalist_points = [cd.points for name, cd in counts.items() if name in finalists]
    return 0.75 * min(finalist_points) if finalist_points else 0.0


def _build_work_nodes(
    visible_steps: list[EphStep],
    first_visible_idx: int,
    finalists: set[str],
    work_first_appearance: dict[str, int],
) -> tuple[list[SankeyNode], dict[str, int], list[set[str]]]:
    """Create nodes for each work at each visible step.

    Returns:
        nodes: The list of SankeyNode dicts.
        node_id_to_idx: Mapping from node id string to index in nodes list.
        active_works_by_step: List of sets of work names active at each step.
    """
    nodes: list[SankeyNode] = []
    node_id_to_idx: dict[str, int] = {}
    active_works: dict[str, CountData] = {}
    active_works_by_step: list[set[str]] = []
    works_to_remove: set[str] = set()

    for relative_idx, (ballots, counts, eliminations) in enumerate(visible_steps):
        step_idx = first_visible_idx + relative_idx

        # Remove works eliminated in the previous step
        for work_name in works_to_remove:
            active_works.pop(work_name, None)

        close_to_advance_threshold = _compute_close_to_advance_threshold(
            counts, finalists
        )

        # Update active works with current step's counts
        active_works.update(counts)

        # Record active set before marking for removal
        active_works_by_step.append(set(active_works))

        # Create a node for every active work
        for work_name, count_data in active_works.items():
            node_id = f"{work_name}_step_{step_idx}"
            node_id_to_idx[node_id] = len(nodes)

            status = _classify_elimination_status(
                work_name,
                count_data,
                eliminations,
                finalists,
                close_to_advance_threshold,
            )

            nodes.append(
                {
                    "id": node_id,
                    "name": work_name,
                    "step": step_idx - first_visible_idx,
                    "display_step": step_idx,
                    "points": count_data.points,
                    "nominations": count_data.nominations,
                    "ballot_count": count_data.ballot_count,
                    "status": status,
                    "is_finalist": work_name in finalists,
                    "first_appearance": work_first_appearance[work_name],
                }
            )

        works_to_remove = set(eliminations)

    return nodes, node_id_to_idx, active_works_by_step


def _build_synthetic_final_step(
    visible_steps: list[EphStep],
    first_visible_idx: int,
    finalists: set[str],
    work_first_appearance: dict[str, int],
    nodes: list[SankeyNode],
    node_id_to_idx: dict[str, int],
    active_works_by_step: list[set[str]],
) -> None:
    """Append a synthetic final step showing only finalists.

    This lets the last elimination's links render properly, since that
    elimination doesn't redistribute its votes.

    Mutates nodes, node_id_to_idx, and active_works_by_step in place.
    """
    if not visible_steps or not finalists:
        return

    final_step_idx = first_visible_idx + len(visible_steps) - 1
    synthetic_step_idx = final_step_idx + 1
    _, final_counts, final_eliminations = visible_steps[-1]

    # Only create synthetic step if the final visible step still has non-finalists
    if not final_eliminations and len(final_counts) <= len(finalists):
        return

    synthetic_active: set[str] = set()

    for work_name in finalists:
        node_id = f"{work_name}_step_{synthetic_step_idx}"
        node_id_to_idx[node_id] = len(nodes)

        count_data = _find_finalist_count_data(work_name, final_counts, visible_steps)

        nodes.append(
            {
                "id": node_id,
                "name": work_name,
                "step": synthetic_step_idx - first_visible_idx,
                "display_step": synthetic_step_idx,
                "points": count_data.points,
                "nominations": count_data.nominations,
                "ballot_count": count_data.ballot_count,
                "status": "finalist",
                "is_finalist": True,
                "first_appearance": work_first_appearance.get(
                    work_name, synthetic_step_idx
                ),
            }
        )
        synthetic_active.add(work_name)

    active_works_by_step.append(synthetic_active)


def _find_finalist_count_data(
    work_name: str,
    final_counts: dict[str, CountData],
    visible_steps: list[EphStep],
) -> CountData:
    """Look up the most recent CountData for a finalist work."""
    if work_name in final_counts:
        return final_counts[work_name]

    # Walk backwards to find the most recent data
    for _ballots, step_counts, _elim in reversed(visible_steps):
        if work_name in step_counts:
            return step_counts[work_name]

    return CountData(points=0, nominations=0, ballot_count=0)


def _build_continuation_links(
    visible_steps: list[EphStep],
    first_visible_idx: int,
    nodes: list[SankeyNode],
    node_id_to_idx: dict[str, int],
    active_works_by_step: list[set[str]],
) -> list[SankeyLink]:
    """Create links connecting the same work across consecutive steps."""
    links: list[SankeyLink] = []

    for relative_idx in range(len(active_works_by_step) - 1):
        current_step_idx = first_visible_idx + relative_idx
        next_step_idx = current_step_idx + 1

        current_active = active_works_by_step[relative_idx]
        next_active = active_works_by_step[relative_idx + 1]

        for work_name in current_active & next_active:
            source_idx = node_id_to_idx[f"{work_name}_step_{current_step_idx}"]
            target_idx = node_id_to_idx[f"{work_name}_step_{next_step_idx}"]

            link_value = _resolve_continuation_value(
                work_name,
                relative_idx,
                visible_steps,
                nodes,
                target_idx,
            )

            links.append(
                {
                    "source": source_idx,
                    "target": target_idx,
                    "value": link_value,
                    "type": "continuation",
                }
            )

    return links


def _resolve_continuation_value(
    work_name: str,
    relative_idx: int,
    visible_steps: list[EphStep],
    nodes: list[SankeyNode],
    target_idx: int,
) -> float:
    """Determine the point value for a continuation link."""
    if relative_idx + 1 < len(visible_steps):
        _, next_counts, _ = visible_steps[relative_idx + 1]
        if work_name in next_counts:
            return next_counts[work_name].points

        # Carried-forward: use source step's points
        _, current_counts, _ = visible_steps[relative_idx]
        if work_name in current_counts:
            return current_counts[work_name].points
        return 0
    else:
        # Synthetic step -- get points from target node
        return nodes[target_idx]["points"]


def _build_redistribution_links(
    visible_steps: list[EphStep],
    first_visible_idx: int,
    nodes: list[SankeyNode],
    node_id_to_idx: dict[str, int],
) -> list[SankeyLink]:
    """Create redistribution links from eliminated works to their top recipients.

    For each elimination, the top 3 recipients by point gain get direct links.
    Any remaining recipients are aggregated into an "Other" leaf node.
    """
    links: list[SankeyLink] = []

    for relative_idx, (_ballots, counts, eliminations) in enumerate(visible_steps):
        if not eliminations:
            continue

        step_idx = first_visible_idx + relative_idx

        # Need next step's counts to compute gains
        if relative_idx + 1 >= len(visible_steps):
            continue
        _, next_counts, _ = visible_steps[relative_idx + 1]

        for work_name in eliminations:
            gains = _compute_redistribution_gains(work_name, counts, next_counts)
            if not gains:
                continue

            source_id = f"{work_name}_step_{step_idx}"
            if source_id not in node_id_to_idx:
                continue
            source_idx = node_id_to_idx[source_id]

            sorted_recipients = sorted(gains.items(), key=lambda x: x[1], reverse=True)
            top_recipients = sorted_recipients[:3]
            other_recipients = sorted_recipients[3:]

            # Direct links to top 3
            for recipient_work, gain in top_recipients:
                target_id = f"{recipient_work}_step_{step_idx + 1}"
                if target_id not in node_id_to_idx:
                    continue
                links.append(
                    {
                        "source": source_idx,
                        "target": node_id_to_idx[target_id],
                        "value": gain,
                        "type": "redistribution",
                    }
                )

            # "Other" node for remaining recipients
            if other_recipients:
                _create_other_node_and_link(
                    work_name,
                    step_idx,
                    first_visible_idx,
                    other_recipients,
                    source_idx,
                    nodes,
                    node_id_to_idx,
                    links,
                )

    return links


def _compute_redistribution_gains(
    eliminated_work: str,
    current_counts: dict[str, CountData],
    next_counts: dict[str, CountData],
) -> dict[str, float]:
    """Compute point gains for each recipient after an elimination."""
    gains: dict[str, float] = {}
    for recipient, recipient_data in next_counts.items():
        current_points = (
            current_counts[recipient].points if recipient in current_counts else 0
        )
        point_gain = recipient_data.points - current_points
        if point_gain > 0:
            gains[recipient] = point_gain
    return gains


def _create_other_node_and_link(
    eliminated_work: str,
    step_idx: int,
    first_visible_idx: int,
    other_recipients: list[tuple[str, float]],
    source_idx: int,
    nodes: list[SankeyNode],
    node_id_to_idx: dict[str, int],
    links: list[SankeyLink],
) -> None:
    """Create an "Other" leaf node aggregating minor redistribution recipients.

    "Other" is placed at the next step and has no outgoing links, avoiding
    d3-sankey BFS depth issues.

    Mutates nodes, node_id_to_idx, and links in place.
    """
    other_gain = sum(gain for _, gain in other_recipients)
    next_step = step_idx + 1
    other_node_id = f"Other_{eliminated_work}_step_{next_step}"
    other_node_idx = len(nodes)
    node_id_to_idx[other_node_id] = other_node_idx

    nodes.append(
        {
            "id": other_node_id,
            "name": f"Other ({eliminated_work})",
            "step": next_step - first_visible_idx,
            "display_step": next_step,
            "points": other_gain,
            "nominations": 0,
            "ballot_count": 0,
            "status": "other",
            "is_finalist": False,
            "first_appearance": next_step,
        }
    )

    links.append(
        {
            "source": source_idx,
            "target": other_node_idx,
            "value": other_gain,
            "type": "redistribution",
        }
    )


def transform_eph_to_sankey(
    steps: list[EphStep],
    finalists: set[str],
    mode: str = "compact",
) -> SankeyData:
    """Transform EPH elimination steps into Sankey diagram data.

    Args:
        steps: EPH elimination steps from constitution_2023.eph().
        finalists: Set of finalist work names.
        mode: Display mode -- "compact" (last 10 steps) or "full" (all steps).

    Returns:
        Dictionary with 'nodes' and 'links' arrays for d3-sankey.
    """

    # we compute the first appearances no matter how many steps we end up showing, because the
    # first_appearance value is used for display ordering in compact mode and needs to be consistent
    # with the full data
    work_first_appearance = _compute_first_appearances(steps)
    visible_steps, first_visible_idx = _select_visible_steps(steps, mode)

    nodes, node_id_to_idx, active_works_by_step = _build_work_nodes(
        visible_steps, first_visible_idx, finalists, work_first_appearance
    )

    _build_synthetic_final_step(
        visible_steps,
        first_visible_idx,
        finalists,
        work_first_appearance,
        nodes,
        node_id_to_idx,
        active_works_by_step,
    )

    continuation_links = _build_continuation_links(
        visible_steps, first_visible_idx, nodes, node_id_to_idx, active_works_by_step
    )

    redistribution_links = _build_redistribution_links(
        visible_steps, first_visible_idx, nodes, node_id_to_idx
    )

    return {"nodes": nodes, "links": continuation_links + redistribution_links}
