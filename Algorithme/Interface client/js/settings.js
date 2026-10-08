
function unlock_save(button) {
    button.disabled = false;
}

function lock_save(button) {
    button.disabled = true;
}

function confirm_delete(setting_preset) {
    button = document.getElementById("deletebutton")
    if (!button) throw new Error('Element #button not found');
    // button.onclick = `del_preset_request('${setting_preset}')`;
    button.setAttribute( "onClick", `javascript: del_preset_request('${setting_preset}')` );
    button.innerHTML = "Confirm deletion on preset ?";
    button.classList.toggle('red', true);
}

function erase_after(element, duration) {
    setTimeout(function() {
        element.innerHTML = '';
    }, duration);
}

function save_setting(inputelement, button, alertelement, setting_name, setting_preset, successspan) {
    const input = inputelement.value;
    if (!isNaN(+input)) {
        send_new_setting(+input, button, setting_name, setting_preset, successspan);
    }
    else {
        alertelement.innerHTML = 'Is not a number !';
        erase_after(alertelement, 5000);
    }
}

function save_preset_name(inputelement, button, alertelement, setting_name, setting_preset, successspan) {
    const input = inputelement.value;
    send_new_setting(input, button, setting_name, setting_preset, successspan);
}

async function send_new_setting(value, button, setting_name, setting_preset, successspan) {
    button.classList.toggle('loading');
    await fetch("/settings", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `setting_preset=${setting_preset}&setting_name=${setting_name}&value=${value}`
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
            lock_save(button);

            settings_dict[setting_preset][setting_name] = value;

            if (setting_name == 'preset_name') {
                settings_dict[value] = settings_dict[setting_preset];
                delete settings_dict[setting_preset];
                update_page(value);
            }
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Detailed error:", error);
            button.classList.toggle('loading');
        });
}

async function set_as_active(setting_name) {
    await fetch("/settings", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `set_as_active_request=${setting_name}`
        })
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // Si tout va bien,
            update_active_key(setting_name);
            update_page(setting_name);
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Detailed error:", error);
        });
}

function get_active_key_setting() {
    for (const key in settings_dict) {
        if (settings_dict[key].is_active) {
            return key;
        }
    }
    return false;
}

function update_active_key(preset_key) {
    for (const key in settings_dict) {
        if (settings_dict[key].is_active) {
            settings_dict[key].is_active = false;
        }
        if (key == preset_key) settings_dict[key].is_active = true;
    }
}

async function add_preset_request() {
    await fetch("/settings", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `add_preset_request`
        })
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // Si tout va bien,
            response.json().then(value => {
                settings_dict = value
                setup_page();
            })
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Detailed error:", error);
        });
}

async function del_preset_request(setting_preset) {
    await fetch("/settings", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `del_preset_request=${setting_preset}`
        })
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // Si tout va bien,
            response.json().then(value => {
                settings_dict = value
                setup_page();
            })
        })
        .catch(error => {
            // Affiche l'erreur à l'utilisateur
            alert(error.message);
            console.error("Detailed error:", error);
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
    if (input.length >0) {
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
if (!searchtagsresults) throw new Error('Element #searchtagsresults not found');
search_tag();


// Page display

function show_presets(selected_setting_key, active_setting_key) {

    const presetDivElement = document.getElementById('presetdiv');
    if (!presetDivElement) throw new Error('Element #presetDivElement not found');
    presetDivElement.innerHTML = `<div class="yourpresettext">Your presets : </div>`;

    for (const key in settings_dict) {
        let isActiveText = '';
        if (key == active_setting_key) isActiveText = "(Active)";
        let isSelectedStyle = '';
        if (key == selected_setting_key) isSelectedStyle = "selected";
        presetDivElement.innerHTML += `
        <button 
            class="presetselectorbtn ${isSelectedStyle}" 
            id="${key}" 
            onclick="update_page('${key}')">
                    ${key} ${isActiveText}
        </button>`;
    }

    presetDivElement.innerHTML += `
        <button class="presetselectorbtn"
            onclick="add_preset_request()">
            +
        </button>`;
}

function show_settings(preset_key) {

    // for (const thing in settings_dict[preset_key]) {
    //     console.log(thing, settings_dict[preset_key][thing]);
    // }

    let disabled_tag_for_defautl = '';
    if (settings_dict[preset_key]['is_default']) {
        settingDivElement.innerHTML = `
        <div class="mainsettingbuttons">
            <button 
                onclick="set_as_active('${preset_key}')" 
                class="githubbutton">
                Set as active
            </button>
            You cannot edit the default settings.
        </div>
        `;
        disabled_tag_for_defautl = 'disabled';
    }
    else {
        settingDivElement.innerHTML = `
        <div class="mainsettingbuttons">
            <button 
                onclick="set_as_active('${preset_key}')" 
                class="githubbutton">
                Set as active
            </button>
            <button id="deletebutton"
                onclick="confirm_delete('${preset_key}')" 
                class="githubbutton">
                Delete preset
            </button>
        </div>
        <div class="settingline">
            Preset name : 
            <input id="presetnameinput"
                class="settinginput"
                onkeyup="unlock_save(document.getElementById('presetnamebutton'))"
                type="text"
                value="${preset_key}"
            >
            <button 
                id="presetnamebutton"
                onclick="save_preset_name(
                        document.getElementById('presetnameinput'),
                        this, 
                        document.getElementById('namepresetalert'),
                        'preset_name',
                        '${preset_key}',
                        document.getElementById('namepresetsuccess')
                        )" 
                class="githubbutton" 
                disabled>
                Save.
            </button>
            <span id="namepresetalert" class="alert"></span>
            <span id="namepresetsuccess" class="success"></span>
        </div>
    `;
    }

    const setting_construction_elements = [
        {
            setting_title : "Like scale",
            input_id : "likescaleinput",
            button_id : "likescalebutton",
            setting_dict_id : "like_scale",
            alert_id : "likescalealert",
            success_id : "likescalesuccess"
        },
        {
            setting_title : "Like min",
            input_id : "likemininput",
            button_id : "likeminbutton",
            setting_dict_id : "like_min",
            alert_id : "likeminalert",
            success_id : "likeminsuccess"
        }, 
        {
            setting_title : "Like max",
            input_id : "likemaxinput",
            button_id : "likemaxbutton",
            setting_dict_id : "like_max",
            alert_id : "likemaxalert",
            success_id : "likemaxsuccess"
        },
        {
            setting_title : "View scale",
            input_id : "viewscaleinput",
            button_id : "viewscalebutton",
            setting_dict_id : "view_scale",
            alert_id : "viewscalealert",
            success_id : "viewscalesuccess"
        },
        {
            setting_title : "View min",
            input_id : "viewmininput",
            button_id : "viewminbutton",
            setting_dict_id : "view_min",
            alert_id : "viewminalert",
            success_id : "viewminsuccess"
        }, 
        {
            setting_title : "View max",
            input_id : "viewmaxinput",
            button_id : "viewmaxbutton",
            setting_dict_id : "view_max",
            alert_id : "viewmaxalert",
            success_id : "viewmaxsuccess"
        },
        {
            setting_title : "Tags scale",
            input_id : "tagscaleinput",
            button_id : "tagscalebutton",
            setting_dict_id : "tags_scale",
            alert_id : "tagscalealert",
            success_id : "tagscalesuccess"
        },
        {
            setting_title : "Tags min",
            input_id : "tagmininput",
            button_id : "tagminbutton",
            setting_dict_id : "tags_min",
            alert_id : "tagminalert",
            success_id : "tagminsuccess"
        }, 
        {
            setting_title : "Tags max",
            input_id : "tagmaxinput",
            button_id : "tagmaxbutton",
            setting_dict_id : "tags_max",
            alert_id : "tagmaxalert",
            success_id : "tagmaxsuccess"
        },
        {
            setting_title : "Has already been seen scale",
            input_id : "habsscaleinput",
            button_id : "habsscalebutton",
            setting_dict_id : "has_already_been_seen_scale",
            alert_id : "habsscalealert",
            success_id : "habsscalesuccess"
        },
        {
            setting_title : "Has already been seen min",
            input_id : "habsmininput",
            button_id : "habsminbutton",
            setting_dict_id : "has_already_been_seen_min",
            alert_id : "habsminalert",
            success_id : "habsminsuccess"
        }, 
        {
            setting_title : "Has already been seen max",
            input_id : "habsmaxinput",
            button_id : "habsmaxbutton",
            setting_dict_id : "has_already_been_seen_max",
            alert_id : "habsmaxalert",
            success_id : "habsmaxsuccess"
        },
        {
            setting_title : "Is following scale",
            input_id : "ifscaleinput",
            button_id : "ifscalebutton",
            setting_dict_id : "is_following_scale",
            alert_id : "ifscalealert",
            success_id : "ifscalesuccess"
        },
        {
            setting_title : "Is following min",
            input_id : "ifmininput",
            button_id : "ifminbutton",
            setting_dict_id : "is_following_min",
            alert_id : "ifminalert",
            success_id : "ifminsuccess"
        }, 
        {
            setting_title : "Is following max",
            input_id : "ifmaxinput",
            button_id : "ifmaxbutton",
            setting_dict_id : "is_following_max",
            alert_id : "ifmaxalert",
            success_id : "ifmaxsuccess"
        }
    ];
    

    for (const setting in setting_construction_elements)
    {
        // console.log(setting, setting_construction_elements[setting]);
        settingDivElement.innerHTML += `
            <div class="settingline">
                ${setting_construction_elements[setting]['setting_title']} : 
                <input id="${setting_construction_elements[setting]['input_id']}"
                        class="settinginput"
                        onkeyup="unlock_save(document.getElementById('${setting_construction_elements[setting]['button_id']}'))"
                        type="text"
                        value="${settings_dict[preset_key][setting_construction_elements[setting]['setting_dict_id']]}"
                        ${disabled_tag_for_defautl}>
                <button 
                    id="${setting_construction_elements[setting]['button_id']}" 
                    onclick="save_setting(
                        document.getElementById('${setting_construction_elements[setting]['input_id']}'),
                        this, 
                        document.getElementById('${setting_construction_elements[setting]['alert_id']}'),
                        '${setting_construction_elements[setting]['setting_dict_id']}',
                        '${preset_key}',
                        document.getElementById('${setting_construction_elements[setting]['success_id']}')
                        )" 
                    class="githubbutton" 
                    disabled>
                    Save.
                </button>
                <span id="${setting_construction_elements[setting]['alert_id']}" class="alert"></span>
                <span id="${setting_construction_elements[setting]['success_id']}" class="success"></span>
            </div>`;
    }

}

function setup_page() {
    const active_setting_key = get_active_key_setting();
    show_presets(active_setting_key, active_setting_key);
    show_settings(active_setting_key);
}

function update_page(selected_setting_key) {
    const active_setting_key = get_active_key_setting();
    show_presets(selected_setting_key, active_setting_key);
    show_settings(selected_setting_key);
}

if (!settings_dict) throw new Error('settings_dict missing.');
const settingDivElement = document.getElementById('settingsdiv');
if (!settingDivElement) throw new Error('Element #settingDivElement not found');

setup_page();