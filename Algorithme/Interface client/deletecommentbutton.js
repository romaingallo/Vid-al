document.querySelectorAll('.deletecommentbutton').forEach(button => {
    button.addEventListener('click', function() {
        const commentId = this.getAttribute('data-comment-id');
        fetch("/api/deletecomment", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `comment_id=${encodeURIComponent(commentId)}`
        })
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Erreur inconnue lors de la suppression.");
                });
            }
            // Si tout va bien, supprime le commentaire du DOM
            this.closest('div[data-id]').remove();
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Erreur détaillée:", error);
        });
    });
});