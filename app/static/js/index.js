document.addEventListener("DOMContentLoaded", () => {
    const searchType = document.getElementById("search_type");
    const forms = {
        summoner: document.getElementById("summoner_form"),
        champion: document.getElementById("champion_form"),
    };

    if (!searchType || !forms.summoner || !forms.champion) {
        return;
    }

    const toggleForm = (selectedType) => {
        Object.entries(forms).forEach(([type, form]) => {
            const isActive = type === selectedType;

            form.hidden = !isActive;

            form.querySelectorAll("input, select, textarea, button").forEach((field) => {
                field.disabled = !isActive;
            });
        });
    };

    toggleForm(searchType.value);
    searchType.addEventListener("change", (event) => {
        toggleForm(event.target.value);
    });
});
