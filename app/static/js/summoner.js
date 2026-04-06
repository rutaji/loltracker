document.addEventListener("DOMContentLoaded", () => {
    const page = document.getElementById("summoner-page");
    if (!page) {
        return;
    }

    let offset = Number(page.dataset.nextOffset);
    const name = page.dataset.name;
    const tagline = page.dataset.tagline;
    const matchList = document.getElementById("match-list");

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

    if (loadMoreButton) {
        loadMoreButton.addEventListener("click", async () => {
            const response = await fetch(`/summoner/${name}/${tagline}?offset=${offset}&ajax=true`);
            const data = await response.json();

            data.matches.forEach(match => {
                const matchDiv = document.createElement("article");
                matchDiv.className = "match";

                const summaryButton = document.createElement("button");
                summaryButton.type = "button";
                summaryButton.className = "match-summary";
                summaryButton.dataset.matchId = match.match_id;
                summaryButton.innerHTML = `
                    <span>Match ${match.match_id}</span>
                    <span>${match.mode}</span>
                    <span>Patch ${match.version}</span>
                `;
                summaryButton.addEventListener("click", () => toggleMatch(match.match_id));

                const detailsDiv = document.createElement("div");
                detailsDiv.id = `match-${match.match_id}`;
                detailsDiv.className = "match-details";
                detailsDiv.style.display = "none";

                let html = `<div class="match-meta"><p><strong>Start:</strong> ${match.start}</p><p><strong>End:</strong> ${match.end}</p></div>`;
                html += `<div class="table-shell"><table>
                    <tr><th>Name</th><th>Champion</th><th>K</th><th>D</th><th>A</th><th>Gold</th><th>Team</th><th>Won</th></tr>`;
                match.participants.forEach(p => {
                    html += `<tr>
                        <td>${p.name}</td>
                        <td>${p.champion}</td>
                        <td>${p.kills}</td>
                        <td>${p.deaths}</td>
                        <td>${p.assists}</td>
                        <td>${p.gold}</td>
                        <td>${p.team}</td>
                        <td>${p.won}</td>
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
