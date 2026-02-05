
function unlock_save(button) {
    button.disabled = false;
}

function lock_save(button) {
    button.disabled = true;
}

function erase_after(element, duration) {
    setTimeout(function() {
        element.innerHTML = '';
    }, duration);
}

function save_setting(inputelement, button, alertelement, setting_name, successspan) {
    const input = inputelement.value;
    if (!isNaN(+input)) {
        send_new_setting(+input, button, setting_name, successspan);
    }
    else {
        alertelement.innerHTML = 'Is not a number !';
        erase_after(alertelement, 5000);
    }
}

async function send_new_setting(value, button, setting_name, successspan) {
    button.classList.toggle('loading');
    await fetch("/settings", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `${setting_name}=${value}`
        })
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // Si tout va bien,
            successspan.innerHTML = 'Saved !';
            erase_after(successspan, 5000);
            button.classList.toggle('loading');
            lock_save(button)
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Detailed error:", error);
            button.classList.toggle('loading');
        });
}