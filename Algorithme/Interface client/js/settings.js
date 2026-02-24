
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

// Tags managment
async function remove_tag(tag_name) {
    fetch("/api/settings/remove_followed_tag", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `tag_name=${tag_name}`
        })
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // Si tout va bien,
            const taglineelement = document.getElementById(`${tag_name}`);
            if (!taglineelement) throw new Error(`Element ${tag_name} introuvable`);
            taglineelement.remove();
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Detailed error:", error);
        });
}

async function search_tag() {
    let input = document.getElementById('searchtagbar').value
    input = input.toLowerCase();
    try {
        const data = await send_search_tag(input);
        searchtagsresults.innerHTML = '';
        data.forEach(element => {
            const li = document.createElement('li');
            li.innerHTML = `${element} <img src="/images/plus_cross.svg" class="imgbuttonicon" alt="+" onclick="add_tag(\'${element}\')">`;
            searchtagsresults.appendChild(li);
        });
        if (data.length==0){
            const li = document.createElement('li');
            li.innerHTML = `${input} <img src="/images/plus_cross.svg" class="imgbuttonicon" alt="+" onclick="add_tag(\'${input}\')">`;
            searchtagsresults.appendChild(li);
        }
    } catch (error) {
        console.error("Error in search_tag:", error);
    }
}


async function send_search_tag(tag_searched) {
    const response = await fetch("/api/search/tag", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `tag_searched=${tag_searched}`
        });

    if (!response.ok) {
        // Si la réponse n'est pas OK, extraire le message d'erreur
        const errorData = await response.json();
        throw new Error(errorData.error || "Erreur inconnue du serveur.");
    }

    // Extraire et retourner les données JSON
    return await response.json();
}

async function add_tag(tag_name) {
    fetch("/api/settings/add_user_followed_tag", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `tag_name=${tag_name}`
        })
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // Si tout va bien,
            const taglist = document.getElementById('taglist');
            if (!taglist) throw new Error('Element #taglist introuvable');
            const li = document.createElement('li');
            li.className = "taglistelement";
            li.id = `${tag_name}`;
            li.innerHTML = `${tag_name}<img src="/images/close_cross.svg" class="imgbuttonicon" alt="X" onclick="remove_tag('${tag_name}')">`;
            taglist.appendChild(li);
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Detailed error:", error);
        });
}

const searchtagsresults = document.getElementById('searchtagsresults');
if (!searchtagsresults) throw new Error('Element #searchtagsresults introuvable');
search_tag();