async function toggle_is_following(channel_followed_username, button) {
    button.classList.toggle('loading');
    fetch("/api/togglefollowing", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `channel_followed_username=${channel_followed_username}`
        })
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 400, 500)
                return response.json().then(err => {
                    // ishiddencheckbox.checked = !ishiddencheckbox.checked;
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // Si tout va bien,
            // let result = response.json();
            button.textContent = button.textContent === "Follow" ? "Unfollow" : "Follow";
            button.classList.toggle('loading');
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Detailed error:", error);
            button.classList.toggle('loading');
        });
    
}