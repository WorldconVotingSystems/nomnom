// Sankey Visualization for EPH Results
(function () {
    "use strict";

    // Configuration
    const config = {
        nodeWidth: 15,
        nodePadding: 10,
        linkOpacity: 0.2,
        linkOpacityHighlight: 0.6,
        linkOpacityDim: 0.05,
        margin: { top: 20, right: 150, bottom: 20, left: 150 },
    };

    // State
    let currentHighlight = null;
    let graph = null;
    let lastStep = 0;
    let sankeyData = null;
    const LABEL_FONT_SIZE = 11;

    // Initialize
    function init() {
        console.log("[Sankey] Starting initialization...");
        console.log("[Sankey] D3 available:", typeof d3 !== "undefined");
        console.log(
            "[Sankey] d3.sankey available:",
            typeof d3 !== "undefined" && typeof d3.sankey !== "undefined",
        );

        // Check for D3
        if (typeof d3 === "undefined") {
            console.error("[Sankey] D3.js library not loaded");
            showError("D3.js library failed to load. Please refresh the page.");
            return;
        }

        // Check for d3-sankey plugin
        if (typeof d3.sankey === "undefined") {
            console.error("[Sankey] d3-sankey plugin not loaded");
            showError(
                "D3 Sankey plugin failed to load. Please refresh the page.",
            );
            return;
        }

        console.log("[Sankey] All dependencies loaded successfully");

        setupControls();
        setupKeyboardNav();

        // Load data from API and render
        loadAndRender(currentMode);
    }

    // Show error message (non-destructive — preserves container DOM for re-fetch)
    function showError(message) {
        const container = document.querySelector(".sankey-viz-container");
        if (container) {
            // Remove any previous error overlay
            const existing = container.querySelector(".sankey-error-overlay");
            if (existing) existing.remove();

            // Hide the SVG but don't destroy it
            const svg = container.querySelector("#sankey-svg");
            if (svg) svg.style.display = "none";

            // Add error overlay
            const overlay = document.createElement("div");
            overlay.className = "sankey-error-overlay";
            overlay.innerHTML = `
                <div style="padding: 40px; text-align: center; color: #721c24; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 6px;">
                    <p style="margin: 0 0 10px 0; font-weight: bold;">⚠ Error Loading Visualization</p>
                    <p style="margin: 0;">${message}</p>
                    <p style="margin: 15px 0 0 0;">
                        <a href="?" style="color: #004085; text-decoration: underline;">Try again</a>
                    </p>
                </div>
            `;
            container.appendChild(overlay);

            // Ensure container looks loaded (hides spinner)
            container.classList.add("loaded");
        }
    }

    // Render Sankey diagram
    function renderSankey() {
        try {
            const container = document.querySelector(".sankey-viz-container");
            const svg = d3.select("#sankey-svg");

            // Clear any error overlay and restore SVG visibility
            const errorOverlay = container.querySelector(".sankey-error-overlay");
            if (errorOverlay) errorOverlay.remove();
            const svgEl = container.querySelector("#sankey-svg");
            if (svgEl) svgEl.style.display = "";

            // Validate data structure
            if (!sankeyData || !sankeyData.nodes || !sankeyData.links) {
                throw new Error("Invalid Sankey data structure");
            }

            if (sankeyData.nodes.length === 0) {
                throw new Error("No data to visualize");
            }

            // Clear previous render
            svg.selectAll("*").remove();

            // Calculate dimensions
            const containerWidth = container.clientWidth;
            const stepsCount =
                Math.max(...sankeyData.nodes.map((n) => n.step)) + 1;
            lastStep = stepsCount - 1;

            // Width calculation: give each step ~150px, minimum container width
            const minWidthPerStep = 150;
            const calculatedWidth = stepsCount * minWidthPerStep;
            const widthWithMargins = Math.max(calculatedWidth, containerWidth);
            const width =
                widthWithMargins - config.margin.left - config.margin.right;

            // Height calculation: scale based on number of nodes
            // Compact mode (~136 nodes) looks good at 600px
            // Full mode (~1274 nodes) needs proportionally more space
            const nodeCount = sankeyData.nodes.length;
            const baseHeight = 600;
            const baseNodeCount = 136;

            // Calculate height based on node density
            // Use a scaling factor that gives reasonable results
            let calculatedHeight;
            if (nodeCount <= baseNodeCount) {
                calculatedHeight = baseHeight;
            } else {
                // Scale up for more nodes, but not linearly (use square root to dampen growth)
                const scaleFactor = Math.sqrt(nodeCount / baseNodeCount);
                calculatedHeight = Math.max(baseHeight * scaleFactor, 1200);
            }

            const containerHeight = calculatedHeight;
            const height =
                containerHeight - config.margin.top - config.margin.bottom;

            // Set SVG size (may be wider than container for scrolling)
            svg.attr("width", widthWithMargins)
                .attr("height", containerHeight)
                .attr("role", "img")
                .attr(
                    "aria-label",
                    "EPH flow visualization showing how points flow through elimination rounds",
                );

            // Add title and description for screen readers
            svg.append("title").text("EPH Flow Visualization");

            svg.append("desc").text(
                "Sankey diagram showing how EPH points flow through elimination rounds, with finalists at the top and eliminated works below.",
            );

            // Create main group
            const g = svg
                .append("g")
                .attr(
                    "transform",
                    `translate(${config.margin.left},${config.margin.top})`,
                );

            // Adjust node padding based on node density
            // More nodes = need less padding to fit, but still keep readable
            const adjustedNodePadding =
                nodeCount > 500 ? 5 : config.nodePadding;

            // Create Sankey generator
            // Note: backend provides numeric indices in links, so we don't specify nodeId
            const sankey = d3
                .sankey()
                .nodeWidth(config.nodeWidth)
                .nodePadding(adjustedNodePadding)
                .extent([
                    [0, 0],
                    [width, height],
                ])
                .nodeSort(customNodeSort)
                .nodeAlign((node) => node.step);

            // Generate Sankey layout
            // nodeAlign uses the 0-based step attribute to assign nodes to columns,
            // so d3-sankey computes both x and y positions correctly in a single pass.
            graph = sankey(sankeyData);

            // Post-layout enforcement: d3-sankey's relaxation can disorder nodes
            // within each column even when nodeSort is defined, because link forces
            // move y-positions and collision resolution uses damping that doesn't
            // fully restore the intended order. Re-sort each column and re-assign
            // y-positions to enforce the sort.
            const layerMap = new Map();
            for (const node of graph.nodes) {
                const layer = node.layer;
                if (!layerMap.has(layer)) layerMap.set(layer, []);
                layerMap.get(layer).push(node);
            }
            for (const [, layerNodes] of layerMap) {
                layerNodes.sort(customNodeSort);
                let y = layerNodes[0]
                    ? Math.min(...layerNodes.map((n) => n.y0))
                    : 0;
                for (const node of layerNodes) {
                    const h = node.y1 - node.y0;
                    node.y0 = y;
                    node.y1 = y + h;
                    y = node.y1 + adjustedNodePadding;
                }
            }
            // Recalculate link positions after moving nodes
            sankey.update(graph);

            // Draw links first (so they appear behind nodes)
            const links = g
                .append("g")
                .attr("class", "links")
                .attr("fill", "none")
                .selectAll("path")
                .data(graph.links)
                .enter()
                .append("path")
                .attr(
                    "class",
                    (d) =>
                        `sankey-link sankey-link-${d.type || "continuation"}`,
                )
                .attr("d", d3.sankeyLinkHorizontal())
                .attr("stroke", (d) => {
                    // Color links based on type
                    if (d.type === "redistribution") {
                        return "#ff9800"; // Orange for redistributed points
                    }
                    return "#999"; // Gray for continuation
                })
                .attr("stroke-width", (d) => Math.max(1, d.width))
                .style("stroke-opacity", config.linkOpacity)
                .append("title")
                .text((d) => {
                    const sourceName = d.source.name;
                    const targetName = d.target.name;
                    const points = d.value.toFixed(2);
                    if (d.type === "redistribution") {
                        return `${sourceName} eliminated → ${points} points to ${targetName}`;
                    }
                    return `${sourceName} → ${targetName}: ${points} points`;
                });

            // Draw nodes
            const nodes = g
                .append("g")
                .attr("class", "nodes")
                .selectAll("g")
                .data(graph.nodes)
                .enter()
                .append("g")
                .attr("class", "node-group")
                .append("rect")
                .attr("class", (d) => `sankey-node ${d.status}`)
                .attr("x", (d) => d.x0)
                .attr("y", (d) => d.y0)
                .attr("width", (d) => d.x1 - d.x0)
                .attr("height", (d) => d.y1 - d.y0)
                .attr("tabindex", "0")
                .attr("role", "button")
                .attr(
                    "aria-label",
                    (d) =>
                        `${d.name}, Step ${d.display_step + 1}, ${d.points.toFixed(2)} points, ${d.status}`,
                )
                .on("click", handleNodeClick)
                .on("mouseover", handleNodeMouseover)
                .on("mouseout", handleNodeMouseout)
                .on("keydown", handleNodeKeydown);

            // Draw node labels (first and last columns only)
            const labelNodes = graph.nodes.filter((d) => {
                if (d.step === 0) {
                    // First column: show if node is tall enough (≥ font height)
                    return d.y1 - d.y0 >= LABEL_FONT_SIZE;
                }
                if (d.step === lastStep) {
                    return true;
                }
                return false;
            });

            const labels = g
                .append("g")
                .attr("class", "labels")
                .selectAll("text")
                .data(labelNodes)
                .enter()
                .append("text")
                .attr("class", "permanent-label")
                .attr("x", (d) => {
                    return d.step === 0 ? d.x1 + 6 : d.x0 - 6;
                })
                .attr("y", (d) => (d.y0 + d.y1) / 2)
                .attr("dy", "0.35em")
                .attr("text-anchor", (d) => (d.step === 0 ? "start" : "end"))
                .text((d) => {
                    const maxLen = 30;
                    return d.name.length > maxLen
                        ? d.name.substring(0, maxLen) + "..."
                        : d.name;
                })
                .style("font-size", LABEL_FONT_SIZE + "px")
                .style("fill", "#495057")
                .style("pointer-events", "none");

            // Hide loading indicator
            if (container) {
                container.classList.add("loaded");
            }
        } catch (error) {
            console.error("Sankey rendering error:", error);
            showError("Failed to render visualization: " + error.message);
        }
    }

    // Custom node sorting: finalists at top, then by status and points descending
    // Note: d3-sankey applies this within each computed depth level
    function customNodeSort(a, b) {
        // If same step, sort by status then points
        const statusOrder = {
            finalist: 0,
            active: 1,
            close: 2,
            early: 3,
            other: 4,
        };
        const statusDiff = statusOrder[a.status] - statusOrder[b.status];
        if (statusDiff !== 0) return statusDiff;
        return b.points - a.points;
    }

    // Handle node click (highlight journey)
    function handleNodeClick(event, d) {
        event.preventDefault();
        // If clicking same work, toggle off
        if (currentHighlight === d.name) {
            clearHighlight();
            return;
        }

        currentHighlight = d.name;
        highlightWork(d.name);
    }

    // Handle keyboard navigation on nodes
    function handleNodeKeydown(event, d) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            handleNodeClick(event, d);
        }
    }

    // Highlight a work's journey through all steps
    function highlightWork(workName) {
        // Remove any hover labels since highlight labels will take over
        d3.selectAll(".hover-label").remove();

        // Highlight nodes
        d3.selectAll(".sankey-node")
            .classed("highlighted", (n) => n.name === workName)
            .classed("dimmed", (n) => n.name !== workName)
            .style("opacity", (n) => (n.name === workName ? 1 : 0.3));

        // Highlight links connected to this work
        d3.selectAll(".sankey-link")
            .classed(
                "highlighted",
                (l) => l.source.name === workName || l.target.name === workName,
            )
            .classed(
                "dimmed",
                (l) => l.source.name !== workName && l.target.name !== workName,
            )
            .style("stroke-opacity", (l) => {
                if (l.source.name === workName || l.target.name === workName) {
                    return config.linkOpacityHighlight;
                }
                return config.linkOpacityDim;
            });

        // Remove any existing highlight labels
        d3.selectAll(".highlight-label").remove();

        // Add labels at every node belonging to this work
        const svg = d3.select("#sankey-svg");
        const labelsGroup = svg.select("g").select(".labels");
        const maxLen = 30;

        const workNodes = graph.nodes.filter((n) => n.name === workName);
        workNodes.forEach((n) => {
            // Skip nodes that already have a visible permanent label
            const isFirstColumn = n.step === 0;
            const isLastColumn = n.step === lastStep;
            const hasPermanentLabel =
                (isFirstColumn && n.y1 - n.y0 >= LABEL_FONT_SIZE) ||
                isLastColumn;

            if (!hasPermanentLabel) {
                labelsGroup
                    .append("text")
                    .attr("class", "highlight-label")
                    .attr("x", isFirstColumn ? n.x1 + 6 : n.x0 - 6)
                    .attr("y", (n.y0 + n.y1) / 2)
                    .attr("dy", "0.35em")
                    .attr("text-anchor", isFirstColumn ? "start" : "end")
                    .text(
                        n.name.length > maxLen
                            ? n.name.substring(0, maxLen) + "..."
                            : n.name,
                    );
            }
        });

        // Dim permanent labels on non-highlighted nodes
        d3.selectAll(".permanent-label").style("opacity", (n) =>
            n.name === workName ? 1 : 0.3,
        );
    }

    // Clear highlighting
    function clearHighlight() {
        currentHighlight = null;

        d3.selectAll(".sankey-node")
            .classed("highlighted", false)
            .classed("dimmed", false)
            .style("opacity", 1);

        d3.selectAll(".sankey-link")
            .classed("highlighted", false)
            .classed("dimmed", false)
            .style("stroke-opacity", config.linkOpacity);

        // Remove highlight labels
        d3.selectAll(".highlight-label").remove();

        // Restore permanent label opacity
        d3.selectAll(".permanent-label").style("opacity", 1);
    }

    // Handle node mouseover (show tooltip)
    function handleNodeMouseover(event, d) {
        // Don't show tooltip if it's an "Other" node
        if (d.name.includes("Other Recipients")) {
            return;
        }

        // Remove any existing tooltip
        d3.selectAll(".sankey-tooltip").remove();

        // Create tooltip
        const tooltip = d3
            .select("body")
            .append("div")
            .attr("class", "sankey-tooltip")
            .style("position", "absolute")
            .style("left", event.pageX + 10 + "px")
            .style("top", event.pageY + 10 + "px")
            .style("background", "rgba(0, 0, 0, 0.9)")
            .style("color", "white")
            .style("padding", "10px")
            .style("border-radius", "6px")
            .style("font-size", "13px")
            .style("pointer-events", "none")
            .style("z-index", "1000")
            .style("box-shadow", "0 2px 8px rgba(0,0,0,0.3)");

        let tooltipHtml = `<strong>${d.name}</strong>`;
        tooltipHtml += `<div style="margin-top: 8px;">EPH Points: ${d.points.toFixed(2)}</div>`;

        // Only show nominations/ballots for non-Other nodes
        if (d.nominations !== undefined) {
            tooltipHtml += `<div>Nominations: ${d.nominations}</div>`;
        }
        if (d.ballot_count !== undefined) {
            tooltipHtml += `<div>Ballots: ${d.ballot_count}</div>`;
        }

        tooltipHtml += `<div>Step: ${d.display_step + 1}</div>`;
        tooltipHtml += `<div style="margin-top: 8px; font-size: 11px; color: #ccc;">Click to highlight journey</div>`;

        tooltip.html(tooltipHtml);

        // Show hover label for intermediate columns (or suppressed first-column nodes)
        // Skip when a highlight is active — highlight labels handle visibility
        const isFirstColumn = d.step === 0;
        const isLastColumn = d.step === lastStep;
        const isIntermediate = !isFirstColumn && !isLastColumn;
        const isSuppressedFirstCol =
            isFirstColumn && d.y1 - d.y0 < LABEL_FONT_SIZE;

        if (!currentHighlight && (isIntermediate || isSuppressedFirstCol)) {
            // Remove any existing hover label
            d3.selectAll(".hover-label").remove();

            const svg = d3.select("#sankey-svg");
            const labelsGroup = svg.select("g").select(".labels");

            const maxLen = 30;
            const labelText =
                d.name.length > maxLen
                    ? d.name.substring(0, maxLen) + "..."
                    : d.name;

            const hoverLabel = labelsGroup
                .append("text")
                .attr("class", "hover-label")
                .attr("x", isFirstColumn ? d.x1 + 6 : d.x0 - 6)
                .attr("y", (d.y0 + d.y1) / 2)
                .attr("dy", "0.35em")
                .attr("text-anchor", isFirstColumn ? "start" : "end")
                .text(labelText);

            // Trigger fade-in: set visible class after a frame so the transition fires
            requestAnimationFrame(() => {
                hoverLabel.classed("visible", true);
            });
        }
    }

    // Handle node mouseout (hide tooltip)
    function handleNodeMouseout() {
        d3.selectAll(".sankey-tooltip").remove();

        // Fade out and remove hover labels
        const hoverLabels = d3.selectAll(".hover-label");
        if (!hoverLabels.empty()) {
            hoverLabels.classed("visible", false);
            // Remove from DOM after transition completes
            setTimeout(() => {
                d3.selectAll(".hover-label").remove();
            }, 160);
        }
    }

    // Show loading spinner
    function showLoading() {
        const container = document.querySelector(".sankey-viz-container");
        if (container) {
            container.classList.remove("loaded");
        }
    }

    // Hide loading spinner
    function hideLoading() {
        const container = document.querySelector(".sankey-viz-container");
        if (container) {
            container.classList.add("loaded");
        }
    }

    // Fetch data from API and render
    function loadAndRender(mode) {
        showLoading();

        const url = new URL(sankeyDataUrl, window.location.origin);
        url.searchParams.set("mode", mode);

        fetch(url)
            .then((response) => {
                if (!response.ok) {
                    return response.json().then((data) => {
                        throw new Error(data.error || `HTTP ${response.status}`);
                    });
                }
                return response.json();
            })
            .then((data) => {
                sankeyData = data;
                try {
                    renderSankey();
                } catch (e) {
                    console.error("Sankey rendering error:", e);
                    showError("Failed to render visualization: " + e.message);
                }
            })
            .catch((error) => {
                console.error("[Sankey] Fetch error:", error);
                showError("Failed to load data: " + error.message);
            });
    }

    // Setup control buttons
    function setupControls() {
        const buttons = document.querySelectorAll(".toggle-btn");
        buttons.forEach((btn) => {
            btn.addEventListener("click", function () {
                const mode = this.dataset.mode;

                // Update active state on buttons
                buttons.forEach((b) => b.classList.remove("active"));
                this.classList.add("active");

                // Track current mode for resize handler
                currentMode = mode;

                // Update URL in address bar without reload (for bookmarkability)
                const url = new URL(window.location);
                url.searchParams.set("mode", mode);
                window.history.replaceState({}, "", url);

                // Re-fetch and re-render
                loadAndRender(mode);
            });
        });
    }

    // Setup keyboard navigation
    function setupKeyboardNav() {
        // Allow Escape to clear highlight
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && currentHighlight) {
                clearHighlight();
            }
        });
    }

    // Handle window resize
    let resizeTimeout;
    window.addEventListener("resize", function () {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function () {
            if (graph && sankeyData) {
                renderSankey();
            }
        }, 250);
    });

    // Initialize on load
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
