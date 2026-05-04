document.addEventListener("DOMContentLoaded", () => {
    const page = document.getElementById("summoner-page");
    if (!page) {
        return;
    }

    let offset = Number(page.dataset.nextOffset);
    let favoriteOffset = Number(page.dataset.favoriteNextOffset);
    const name = page.dataset.name;
    const tagline = page.dataset.tagline;
    const puuid = page.dataset.puuid;
    const matchQueueFilter = page.dataset.matchQueueFilter || "all";
    const favoriteQueueFilter = page.dataset.favoriteQueueFilter || "ranked_solo";
    const matchList = document.getElementById("match-list");
    const favoriteChampionList = document.getElementById("favorite-champion-list");
    const refreshButton = document.getElementById("refresh-matches");
    const refreshStatus = document.getElementById("refresh-status");
    const matchQueueFilterSelect = document.getElementById("match-queue-filter");
    const favoriteQueueFilterSelect = document.getElementById("favorite-queue-filter");
    const loadedGamesValue = document.getElementById("loaded-games");
    const loadedWinrateValue = document.getElementById("loaded-winrate");
    const loadedKdaValue = document.getElementById("loaded-kda");
    const refreshMessageStorageKey = `summoner-refresh:${name}#${tagline}`;

    function buildSummonerUrl(
        baseOffset = 0,
        ajax = false,
        selectedMatchQueueFilter = matchQueueFilter,
        selectedFavoriteQueueFilter = favoriteQueueFilter
    ) {
        const params = new URLSearchParams();
        if (baseOffset > 0) {
            params.set("offset", String(baseOffset));
        }
        if (ajax) {
            params.set("ajax", "true");
        }
        if (selectedMatchQueueFilter) {
            params.set("match_queue_filter", selectedMatchQueueFilter);
        }
        if (selectedFavoriteQueueFilter) {
            params.set("favorite_queue_filter", selectedFavoriteQueueFilter);
        }

        const query = params.toString();
        if (!query) {
            return `/summoner/${encodeURIComponent(name)}/${encodeURIComponent(tagline)}`;
        }

        return `/summoner/${encodeURIComponent(name)}/${encodeURIComponent(tagline)}?${query}`;
    }

    function buildFavoriteChampionsUrl(baseOffset = 0, selectedFavoriteQueueFilter = favoriteQueueFilter) {
        const params = new URLSearchParams();
        if (baseOffset > 0) {
            params.set("offset", String(baseOffset));
        }
        if (selectedFavoriteQueueFilter) {
            params.set("favorite_queue_filter", selectedFavoriteQueueFilter);
        }

        const query = params.toString();
        const baseUrl = `/summoner/${encodeURIComponent(name)}/${encodeURIComponent(tagline)}/favorite-champions`;
        return query ? `${baseUrl}?${query}` : baseUrl;
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

    function formatCompactDecimal(value, maximumFractionDigits = 2) {
        const number = readNumber(value);
        return number.toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits
        });
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function buildParticipantUrl(participant) {
        return `/summoner/${encodeURIComponent(participant.name || "")}/${encodeURIComponent(participant.tagline || "")}`;
    }

    function buildItemImagePath(itemId) {
        const normalizedId = Number(itemId) || 0;
        return normalizedId > 0 ? `/static/img/items/${normalizedId}.png` : "";
    }

    function buildParticipantItemsHtml(participant) {
        const items = Array.isArray(participant.items) ? participant.items : [];
        return `<div class="item-strip">${items.map((item) => {
            const itemId = Number(item?.id) || 0;
            const itemImagePath = buildItemImagePath(itemId);
            const classes = [
                "item-slot",
                itemImagePath ? "" : "item-slot--empty",
                item?.isRoleBound ? "item-slot--role" : ""
            ].filter(Boolean).join(" ");
            const itemName = escapeHtml(item?.name || "");
            const itemDescription = escapeHtml(item?.description || "");
            const itemSlot = escapeHtml(item?.slot || "");
            const imageHtml = itemImagePath
                ? `<img src="${escapeHtml(itemImagePath)}" alt="${itemName || itemSlot}" loading="lazy">`
                : ``;
            return `<span class="${classes}" data-item-id="${itemId}" data-item-name="${itemName}" data-item-description="${itemDescription}" data-item-slot="${itemSlot}">${imageHtml}</span>`;
        }).join("")}</div>`;
    }

    function buildFavoriteChampionRowHtml(favorite) {
        const gamesPlayed = readNumber(favorite.games_played);
        const wins = readNumber(favorite.wins);
        const kills = readNumber(favorite.kills);
        const deaths = readNumber(favorite.deaths);
        const assists = readNumber(favorite.assists);
        const winrate = gamesPlayed > 0 ? (wins / gamesPlayed) * 100 : 0;
        const kda = (kills + assists) / Math.max(1, deaths);
        const averageKills = gamesPlayed > 0 ? kills / gamesPlayed : 0;
        const averageDeaths = gamesPlayed > 0 ? deaths / gamesPlayed : 0;
        const averageAssists = gamesPlayed > 0 ? assists / gamesPlayed : 0;
        const championImageHtml = favorite.championImagePath
            ? `<img src="${escapeHtml(favorite.championImagePath)}" alt="${escapeHtml(favorite.champion_name)}" class="champion-avatar" loading="lazy">`
            : ``;
        const championUrl = `/champion/${encodeURIComponent(favorite.champion_name || "")}`;

        return `<tr class="favorite-champion-row">
            <td class="favorite-champion-cell favorite-champion-cell--identity">
                <a href="${championUrl}" class="champion-link favorite-champion-name">${championImageHtml}<span>${escapeHtml(favorite.champion_name)}</span></a>
            </td>
            <td class="favorite-champion-cell favorite-champion-cell--kda">
                <div class="favorite-champion-stat">
                    <div class="favorite-champion-primary">${formatCompactDecimal(kda, 2)} <span>KDA</span></div>
                    <div class="favorite-champion-substat">${formatCompactDecimal(averageKills, 1)}/${formatCompactDecimal(averageDeaths, 1)}/${formatCompactDecimal(averageAssists, 1)}</div>
                </div>
            </td>
            <td class="favorite-champion-cell favorite-champion-cell--results">
                <div class="favorite-champion-stat">
                    <div class="favorite-champion-primary">${formatCompactDecimal(winrate, 2)}%</div>
                    <div class="favorite-champion-substat">${gamesPlayed} games</div>
                </div>
            </td>
        </tr>`;
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

    if (matchQueueFilterSelect) {
        matchQueueFilterSelect.addEventListener("change", () => {
            window.location.assign(buildSummonerUrl(0, false, matchQueueFilterSelect.value, favoriteQueueFilter));
        });
    }

    if (favoriteQueueFilterSelect) {
        favoriteQueueFilterSelect.addEventListener("change", () => {
            window.location.assign(buildSummonerUrl(0, false, matchQueueFilter, favoriteQueueFilterSelect.value));
        });
    }

    const loadMoreButton = document.getElementById("load-more");
    const loadMoreFavoritesButton = document.getElementById("load-more-favorites");

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
                    const refreshedUrl = new URL(buildSummonerUrl(0, false, matchQueueFilter, favoriteQueueFilter), window.location.origin);
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
            const response = await fetch(buildSummonerUrl(offset, true, matchQueueFilter, favoriteQueueFilter));
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
                    <tr><th>Name</th><th>Champion</th><th>K</th><th>D</th><th>A</th><th>Gold</th><th>Items</th><th>Team</th><th>Won</th></tr>`;
                match.participants.forEach((participant) => {
                    const selfBadge = participant.puuid === puuid ? `<span class="player-badge">You</span>` : ``;
                    const participantUrl = buildParticipantUrl(participant);
                    const participantName = escapeHtml(participant.name);
                    const championImageHtml = participant.championImagePath
                        ? `<img src="${participant.championImagePath}" alt="${participant.champion}" class="champion-avatar" loading="lazy">`
                        : ``;
                    html += `<tr class="${getParticipantRowClass(participant)}">
                        <td><a class="participant-link" href="${participantUrl}">${participantName}</a> ${selfBadge}</td>
                        <td><a href="/champion/${encodeURIComponent(participant.champion)}" class="champion-link">${championImageHtml}<span>${escapeHtml(participant.champion)}</span></a></td>
                        <td>${escapeHtml(participant.kills)}</td>
                        <td>${escapeHtml(participant.deaths)}</td>
                        <td>${escapeHtml(participant.assists)}</td>
                        <td>${escapeHtml(participant.gold)}</td>
                        <td>${buildParticipantItemsHtml(participant)}</td>
                        <td>${escapeHtml(participant.team)}</td>
                        <td>${escapeHtml(participant.won)}</td>
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

    if (loadMoreFavoritesButton) {
        loadMoreFavoritesButton.addEventListener("click", async () => {
            loadMoreFavoritesButton.disabled = true;
            const response = await fetch(buildFavoriteChampionsUrl(favoriteOffset, favoriteQueueFilter));
            const data = await response.json();

            data.champions.forEach((favorite) => {
                favoriteChampionList.insertAdjacentHTML("beforeend", buildFavoriteChampionRowHtml(favorite));
            });

            favoriteOffset = data.nextOffset;

            if (!data.hasMore) {
                loadMoreFavoritesButton.style.display = "none";
            } else {
                loadMoreFavoritesButton.disabled = false;
            }
        });
    }

});
