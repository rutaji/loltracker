document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("version-select");
    const tableBody = document.getElementById("stats-body");

    select.addEventListener("change", async () => {
        const version = select.value;

        const response = await fetch(
            `/champion/{{ championData.name }}?version=${version}&ajax=true`
        );

        const data = await response.json();

        tableBody.innerHTML = "";

        data.championStats.forEach(stat => {
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${stat.version}</td>
                <td>${stat.gamemode}</td>
                <td>${stat.gamesPlayed}</td>
                <td>${((stat.wins / (stat.gamesPlayed)) * 100).toFixed(2)}%</td>
                <td>${((stat.kills + stat.assists) / (stat.deaths || 1)).toFixed(2)}</td>
                <td>${(stat.gamesPlayed / stat.matchesAnalyzed * 100).toFixed(2)}%</td>
                <td>${(stat.matchesAnalyzed ? (stat.banned / stat.matchesAnalyzed * 100) : 0).toFixed(2)}%</td>
            `;

            tableBody.appendChild(row);
        });
    });
});