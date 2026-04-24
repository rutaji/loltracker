document.addEventListener("DOMContentLoaded", () => {
    const page = document.body;
    const championName = page.dataset.championName;
    const initialVersion = page.dataset.selectedVersion;

    const versionSelect = document.getElementById("version-select");
    const tableBody = document.getElementById("stats-body");
    const chartInstances = {};
    const initialTrendSeries = parseJsonScript("initial-trend-series", []);

    if (!versionSelect || !tableBody) {
        console.error("Champion page is missing required elements for stats rendering.");
        return;
    }

    const chartConfigs = {
        "chart-winrate": { key: "winrate", label: "Win Rate (%)", type: "line" },
        "chart-pickrate": { key: "pickrate", label: "Pick Rate (%)", type: "line" },
        "chart-banrate": { key: "banrate", label: "Ban Rate (%)", type: "line" },
        "chart-kda": { key: "kda", label: "KDA", type: "line" },
        "chart-total-matches": { key: "totalMatchesPlayed", label: "Total Matches Played", type: "bar" },
    };

    const palette = [
        "#7ed957",
        "#5ea2ff",
        "#ffbe57",
        "#ef6f6c",
        "#9f7aea",
        "#06d6a0",
        "#ff9f1c",
        "#3dd5f3",
    ];

    function parseJsonScript(elementId, fallback) {
        const script = document.getElementById(elementId);
        if (!script) {
            return fallback;
        }

        try {
            return JSON.parse(script.textContent || "null") ?? fallback;
        } catch (error) {
            console.error(`Failed to parse JSON from #${elementId}.`, error);
            return fallback;
        }
    }

    function normalizeSeries(seriesByQueue) {
        if (!Array.isArray(seriesByQueue)) {
            return [];
        }

        return seriesByQueue
            .filter((series) => series && Array.isArray(series.points))
            .map((series) => ({
                queueDescription: series.queueDescription || "Unknown Queue",
                points: series.points.filter((point) => point && point.version),
            }))
            .filter((series) => series.points.length > 0);
    }

    function versionSortKey(version) {
        return version
            .split(".")
            .map((part) => Number.parseInt(part, 10))
            .map((value) => (Number.isNaN(value) ? 0 : value));
    }

    function compareVersionsAscending(versionA, versionB) {
        const aParts = versionSortKey(versionA);
        const bParts = versionSortKey(versionB);
        const maxLength = Math.max(aParts.length, bParts.length);

        for (let index = 0; index < maxLength; index += 1) {
            const a = aParts[index] ?? 0;
            const b = bParts[index] ?? 0;
            if (a !== b) {
                return a - b;
            }
        }

        return 0;
    }

    function formatNumber(value, suffix = "") {
        if (value === null || value === undefined) {
            return "-";
        }
        return `${Number(value).toFixed(2)}${suffix}`;
    }

    function setChampionImages(imagePath) {
        const portraitElements = document.querySelectorAll("[data-champion-image]");
        portraitElements.forEach((imageElement) => {
            const shell = imageElement.parentElement;
            if (imagePath) {
                imageElement.src = imagePath;
                if (shell) {
                    shell.classList.remove("hidden");
                }
            } else if (shell) {
                shell.classList.add("hidden");
            }
        });
    }

    function renderTable(rows) {
        tableBody.innerHTML = "";

        if (!rows || rows.length === 0) {
            const row = document.createElement("tr");
            row.innerHTML = '<td colspan="7">No statistics available for this version.</td>';
            tableBody.appendChild(row);
            return;
        }

        rows.forEach((stat) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${stat.version}</td>
                <td>${stat.queueDescription}</td>
                <td>${stat.totalMatchesPlayed ?? stat.gamesPlayed}</td>
                <td>${formatNumber(stat.winrate, "%")}</td>
                <td>${formatNumber(stat.kda)}</td>
                <td>${formatNumber(stat.pickrate, "%")}</td>
                <td>${formatNumber(stat.banrate, "%")}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    function renderCharts(seriesByQueue) {
        if (typeof Chart === "undefined") {
            console.error("Chart.js is unavailable; skipping chart rendering.");
            return;
        }

        const safeSeries = normalizeSeries(seriesByQueue);

        Object.values(chartInstances).forEach((chart) => chart.destroy());
        Object.keys(chartInstances).forEach((key) => delete chartInstances[key]);

        const allVersions = [...new Set(
            safeSeries.flatMap((series) =>
                series.points.map((point) => point.version)
            )
        )].sort(compareVersionsAscending);

        if (allVersions.length === 0) {
            return;
        }

        Object.entries(chartConfigs).forEach(([canvasId, config]) => {
            const canvas = document.getElementById(canvasId);
            if (!canvas) {
                return;
            }

            const context = canvas.getContext("2d");
            if (!context) {
                console.error(`Canvas 2D context is unavailable for '${canvasId}'.`);
                return;
            }

            const datasets = safeSeries.map((series, index) => {
                const valueByVersion = new Map(
                    series.points.map((point) => [point.version, point[config.key]])
                );
                const color = palette[index % palette.length];

                return {
                    label: series.queueDescription,
                    data: allVersions.map((version) => valueByVersion.get(version) ?? null),
                    borderColor: color,
                    backgroundColor: `${color}55`,
                    tension: 0.28,
                    fill: false,
                    spanGaps: true,
                    borderWidth: 2,
                    pointRadius: config.type === "line" ? 3 : 0,
                };
            });

            try {
                chartInstances[canvasId] = new Chart(context, {
                    type: config.type,
                    data: {
                        labels: allVersions,
                        datasets,
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: config.type === "bar" ? 3.1 : 2.2,
                        scales: {
                            x: {
                                ticks: { color: "#dce7f2" },
                                grid: { color: "rgba(255, 255, 255, 0.08)" },
                            },
                            y: {
                                ticks: { color: "#dce7f2" },
                                grid: { color: "rgba(255, 255, 255, 0.08)" },
                            },
                        },
                        plugins: {
                            legend: {
                                labels: { color: "#edf3fa" },
                            },
                            tooltip: {
                                callbacks: {
                                    label(context) {
                                        const value = context.parsed.y;
                                        if (config.key === "winrate" || config.key === "pickrate" || config.key === "banrate") {
                                            return `${context.dataset.label}: ${formatNumber(value, "%")}`;
                                        }
                                        if (config.key === "kda") {
                                            return `${context.dataset.label}: ${formatNumber(value)}`;
                                        }
                                        return `${context.dataset.label}: ${Math.round(value ?? 0)}`;
                                    },
                                },
                            },
                        },
                    },
                });
            } catch (error) {
                console.error(`Failed to render chart '${canvasId}'.`, error);
            }
        });

        if (Object.keys(chartInstances).length === 0) {
            console.error("No chart instances were created.", { safeSeries, allVersions });
        }
    }

    async function loadVersion(version) {
        const response = await fetch(
            `/champion/${encodeURIComponent(championName)}?version=${encodeURIComponent(version)}&ajax=true`
        );

        if (!response.ok) {
            throw new Error("Failed to load champion stats.");
        }

        const payload = await response.json();

        if (Array.isArray(payload.availableVersions) && payload.availableVersions.length > 0) {
            const current = versionSelect.value;
            versionSelect.innerHTML = payload.availableVersions
                .map((patch) => `<option value="${patch}">${patch}</option>`)
                .join("");
            versionSelect.value = payload.selectedVersion || current;
        }

        renderTable(payload.selectedVersionStats || payload.championStats || []);
        renderCharts(payload.trendSeriesByQueue || []);
        setChampionImages(payload.championImagePath || "");
    }

    versionSelect.addEventListener("change", () => {
        loadVersion(versionSelect.value).catch((error) => {
            console.error("Failed to switch champion version.", error);
            tableBody.innerHTML = `<tr><td colspan="7">${error.message}</td></tr>`;
        });
    });

    // Bootstrap from server-side data so charts are visible even before the first AJAX refresh.
    renderCharts(initialTrendSeries);

    loadVersion(initialVersion || versionSelect.value).catch((error) => {
        console.error("Failed to load champion version.", error);
        tableBody.innerHTML = `<tr><td colspan="7">${error.message}</td></tr>`;
    });
});
