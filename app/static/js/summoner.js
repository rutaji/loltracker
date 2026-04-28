document.addEventListener("DOMContentLoaded", () => {
    const page = document.getElementById("summoner-page");
    if (!page) {
        return;
    }

    let offset = Number(page.dataset.nextOffset);
    const name = page.dataset.name;
    const tagline = page.dataset.tagline;
    const puuid = page.dataset.puuid;
    const queueFilter = page.dataset.queueFilter || "all";
    const matchList = document.getElementById("match-list");
    const refreshButton = document.getElementById("refresh-matches");
    const refreshStatus = document.getElementById("refresh-status");
    const queueFilterSelect = document.getElementById("queue-filter");
    const loadedGamesValue = document.getElementById("loaded-games");
    const loadedWinrateValue = document.getElementById("loaded-winrate");
    const loadedKdaValue = document.getElementById("loaded-kda");
    const refreshMessageStorageKey = `summoner-refresh:${name}#${tagline}`;

    function buildSummonerUrl(baseOffset = 0, ajax = false, selectedQueueFilter = queueFilter) {
        const params = new URLSearchParams();
        if (baseOffset > 0) {
            params.set("offset", String(baseOffset));
        }
        if (ajax) {
            params.set("ajax", "true");
        }
        if (selectedQueueFilter && selectedQueueFilter !== "all") {
            params.set("queue_filter", selectedQueueFilter);
        }

        const query = params.toString();
        if (!query) {
            return `/summoner/${encodeURIComponent(name)}/${encodeURIComponent(tagline)}`;
        }

        return `/summoner/${encodeURIComponent(name)}/${encodeURIComponent(tagline)}?${query}`;
    }

    function setRefreshStatus(message) {
        if (refreshStatus) {
            refreshStatus.textContent = message;
        }
    }

    function readNumber(value) {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : 0;
    }

    function formatDecimal(value) {
        return value.toFixed(2);
    }

    function updateLoadedMatchSummary() {
        if (!loadedGamesValue || !loadedWinrateValue || !loadedKdaValue) {
            return;
        }

        const matchCards = Array.from(matchList.querySelectorAll(".match"));
        let wins = 0;
        let kills = 0;
        let deaths = 0;
        let assists = 0;

        matchCards.forEach((matchCard) => {
            kills += readNumber(matchCard.dataset.playerKills);
            deaths += readNumber(matchCard.dataset.playerDeaths);
            assists += readNumber(matchCard.dataset.playerAssists);

            if (matchCard.dataset.playerWon === "true") {
                wins += 1;
            }
        });

        const gamesShown = matchCards.length;
        const winrate = gamesShown > 0 ? (wins / gamesShown) * 100 : 0;
        const kda = (kills + assists) / Math.max(1, deaths);

        loadedGamesValue.textContent = String(gamesShown);
        loadedWinrateValue.textContent = `${formatDecimal(winrate)}%`;
        loadedKdaValue.textContent = formatDecimal(kda);
    }

    const persistedRefreshMessage = sessionStorage.getItem(refreshMessageStorageKey);
    if (persistedRefreshMessage) {
        setRefreshStatus(persistedRefreshMessage);
        sessionStorage.removeItem(refreshMessageStorageKey);
    }

    function getMatchResult(match) {
        const viewedParticipant = match.participants.find((participant) => participant.puuid === puuid);
        if (!viewedParticipant) {
            return "unknown";
        }
        return viewedParticipant.won ? "win" : "loss";
    }

    function getParticipantRowClass(participant) {
        const rowClasses = ["participant-row", `team-${participant.team}`];
        if (participant.puuid === puuid) {
            rowClasses.push("participant-row--self");
        }
        return rowClasses.join(" ");
    }

    function toggleMatch(id) {
        const el = document.getElementById("match-" + id);
        el.style.display = (el.style.display === "none") ? "block" : "none";
    }

    document.querySelectorAll(".match-summary").forEach((button) => {
        button.addEventListener("click", () => {
            toggleMatch(button.dataset.matchId);
        });
    });

    updateLoadedMatchSummary();

    if (queueFilterSelect) {
        queueFilterSelect.addEventListener("change", () => {
            window.location.assign(buildSummonerUrl(0, false, queueFilterSelect.value));
        });
    }

    const loadMoreButton = document.getElementById("load-more");

    if (refreshButton) {
        refreshButton.addEventListener("click", async () => {
            refreshButton.disabled = true;
            refreshButton.textContent = "Refreshing...";
            setRefreshStatus("");

            try {
                const response = await fetch(`/summoner/${name}/${tagline}/refresh`, {
                    method: "POST"
                });

                if (!response.ok) {
                    throw new Error("Refresh failed");
                }

                const data = await response.json();
                const matchLabel = data.insertedCount === 1 ? "match" : "matches";
                const refreshMessage = `Added ${data.insertedCount} new ${matchLabel}.`;
                const refreshedName = data.summonerName ?? name;
                const refreshedTagline = data.summonerTagline ?? tagline;
                const summonerRouteChanged = refreshedName !== name || refreshedTagline !== tagline;
                const refreshedRefreshMessageStorageKey = `summoner-refresh:${refreshedName}#${refreshedTagline}`;
                if (data.insertedCount > 0 || summonerRouteChanged) {
                    sessionStorage.setItem(refreshedRefreshMessageStorageKey, refreshMessage);
                    const refreshedUrl = new URL(buildSummonerUrl(0, false, queueFilter), window.location.origin);
                    refreshedUrl.pathname = `/summoner/${encodeURIComponent(refreshedName)}/${encodeURIComponent(refreshedTagline)}`;
                    window.location.assign(refreshedUrl.pathname + refreshedUrl.search);
                    return;
                }

                setRefreshStatus(refreshMessage);
                refreshButton.disabled = false;
                refreshButton.textContent = "Refresh Data";
            } catch (error) {
                setRefreshStatus("Refresh failed. Please try again.");
                refreshButton.disabled = false;
                refreshButton.textContent = "Refresh Data";
            }
        });
    }

    if (loadMoreButton) {
        loadMoreButton.addEventListener("click", async () => {
            const response = await fetch(buildSummonerUrl(offset, true, queueFilter));
            const data = await response.json();

            data.matches.forEach((match) => {
                const matchResult = getMatchResult(match);
                const matchDiv = document.createElement("article");
                matchDiv.className = `match match--${matchResult}`;
                const viewedParticipant = match.participants.find((participant) => participant.puuid === puuid);
                matchDiv.dataset.playerKills = String(viewedParticipant?.kills ?? 0);
                matchDiv.dataset.playerDeaths = String(viewedParticipant?.deaths ?? 0);
                matchDiv.dataset.playerAssists = String(viewedParticipant?.assists ?? 0);
                matchDiv.dataset.playerWon = viewedParticipant?.won ? "true" : "false";

                const summaryButton = document.createElement("button");
                summaryButton.type = "button";
                summaryButton.className = `match-summary match-summary--${matchResult}`;
                summaryButton.dataset.matchId = match.match_id;
                summaryButton.innerHTML = `
                    <span>Match ${match.match_id}</span>
                    <span>${match.queueDescription}</span>
                    <span>${matchResult.charAt(0).toUpperCase() + matchResult.slice(1)} | Patch ${match.version}</span>
                `;
                summaryButton.addEventListener("click", () => toggleMatch(match.match_id));

                const detailsDiv = document.createElement("div");
                detailsDiv.id = `match-${match.match_id}`;
                detailsDiv.className = "match-details";
                detailsDiv.style.display = "none";

                let html = `<div class="match-meta"><p><strong>Start:</strong> ${match.start}</p><p><strong>End:</strong> ${match.end}</p></div>`;
                html += `<div class="table-shell"><table>
                    <tr><th>Name</th><th>Champion</th><th>K</th><th>D</th><th>A</th><th>Gold</th><th>Team</th><th>Won</th></tr>`;
                match.participants.forEach((participant) => {
                    const selfBadge = participant.puuid === puuid ? `<span class="player-badge">You</span>` : ``;
                    html += `<tr class="${getParticipantRowClass(participant)}">
                        <td>${participant.name} ${selfBadge}</td>
                        <td>${participant.champion}</td>
                        <td>${participant.kills}</td>
                        <td>${participant.deaths}</td>
                        <td>${participant.assists}</td>
                        <td>${participant.gold}</td>
                        <td>${participant.team}</td>
                        <td>${participant.won}</td>
                    </tr>`;
                });
                html += `</table></div>`;

                detailsDiv.innerHTML = html;

                matchDiv.appendChild(summaryButton);
                matchDiv.appendChild(detailsDiv);
                matchList.appendChild(matchDiv);
            });

            offset = data.nextOffset;

            if (!data.hasMore) {
                loadMoreButton.style.display = "none";
            }

            updateLoadedMatchSummary();
        });
    }
});
