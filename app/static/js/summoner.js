document.addEventListener("DOMContentLoaded", () => {
    const page = document.getElementById("summoner-page");
    if (!page) {
        return;
    }

    let offset = Number(page.dataset.nextOffset);
    const name = page.dataset.name;
    const tagline = page.dataset.tagline;
    const puuid = page.dataset.puuid;
    const matchList = document.getElementById("match-list");
    const refreshButton = document.getElementById("refresh-matches");
    const refreshStatus = document.getElementById("refresh-status");
    const refreshMessageStorageKey = `summoner-refresh:${name}#${tagline}`;

    function setRefreshStatus(message) {
        if (refreshStatus) {
            refreshStatus.textContent = message;
        }
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
                    window.location.assign(`/summoner/${encodeURIComponent(refreshedName)}/${encodeURIComponent(refreshedTagline)}`);
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
            const response = await fetch(`/summoner/${name}/${tagline}?offset=${offset}&ajax=true`);
            const data = await response.json();

            data.matches.forEach((match) => {
                const matchResult = getMatchResult(match);
                const matchDiv = document.createElement("article");
                matchDiv.className = `match match--${matchResult}`;

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
        });
    }
});
