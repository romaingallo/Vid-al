
// Génère des cartes d'exemple dans #gridcontent
const gridcontent = document.getElementById('gridcontent');
if (!gridcontent) throw new Error('Element #gridcontent introuvable');

let isLoading = false;
let endReached = false;
let offset = 0;
let observer;

// const params = new URLSearchParams(window.location.search);
// const channelId = params.get('channel');

async function loadFromServer() {
    if (isLoading || endReached) return;
    isLoading = true;
    try {
        const rootMarginPx = 400;
        while (true) {
            let url = '/api/videos';
            if (typeof channel_name !== 'undefined') {
                url = `/api/channel/${channel_name}/` + offset;
            }
            if (typeof fecth_for_followed !== 'undefined') {
                url = `/api/followedvideos/` + offset;
            }
            offset += 6;
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json(); // attendre un tableau d'objets vidéo

            if (!Array.isArray(data) || data.length === 0) {
                // plus de contenu à charger -> arrêter l'observer
                endReached = true;
                if (observer) observer.disconnect();
                break;
            }

            for (const [i, v] of data.entries()) {
                const card = await createCard(i + 1, v);
                grid.appendChild(card);
            }
            // si le sentinel n'existe pas encore, sortir (ex: premier chargement avant création)
            if (typeof sentinel === 'undefined' || !sentinel) break;

            // si le sentinel est toujours dans la zone de préchargement, boucler et charger une autre page
            const rect = sentinel.getBoundingClientRect();
            const viewportBottom = window.innerHeight + rootMarginPx;
            if (rect.top > viewportBottom) break;

            // sinon la boucle continue et on refait une requête
            if (endReached) break;
        }
    } catch (err) {
        console.error('Échec de chargement des vidéos:', err);
    } finally {
        isLoading = false;
    }
}

async function loadTitleFromHost(videoId, hostURL) {
    try {
        const res = await fetch(`${hostURL}/meta/${videoId}`); // changer l'URL si besoin
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        return `${data.title}`;
    } catch (err) {
        console.error('Échec de chargement des metadonnées:', err);
    }
}

async function loadDataFromYoutube(videoId) {
    try {
        const res = await fetch(`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`); // changer l'URL si besoin
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        return data;
    } catch (err) {
        console.error('Échec de chargement des metadonnées:', err);
    }
}


const thumbPath = './images/miniatures/miniature0.jpg';
async function createCard(i, data = null) {
    const is_youtube_video = data?.is_youtube_video ?? `false`;
    let is_youtube_video_icone = ``;
    let thumb = `${data?.hostURL}/thumbnail/${data?.url}`;
    let channel = data?.channel ?? 'Chaîne';
    let title = `Loading title ?`;
    let channelurl = `/visit_channel/${channel}`;
    let first_upload_date = data?.first_upload;
    let first_upload_date_text = ``;
    const has_already_been_seen = data?.has_already_been_seen ?? false;
    let has_already_been_seen_icon = ``;
    if (has_already_been_seen)
    {
        has_already_been_seen_icon = `<img class="hasbeenseenicon" title="You have already seen this video." src="/images/check_white.svg" alt="Has been seen">`;
    }
    if (first_upload_date)
    {
        first_upload_date_text = ` • ${first_upload_date}`;
    }
    if (is_youtube_video == true) 
        {
            is_youtube_video_icone = `<img class="isfromyoutubeicon" src="/images/favicon.ico" alt="From Youtube">`;
            thumb = `https://i.ytimg.com/vi/${data?.url}/hqdefault.jpg`;
            const data_from_youtube = await loadDataFromYoutube(data?.url);
            title = data_from_youtube?.title ?? `Erreur de titre`;
            if (channel == 'UnknownFromYoutube')
            {
                channel = data_from_youtube?.author_name ?? `Erreur de nom`;
                channelurl = data_from_youtube?.author_url ?? ``;
            }
        }
    else
    {
        title = await loadTitleFromHost(data?.url, data?.hostURL) ?? `Erreur de titre`;
    }
    const url = `/watch/${data?.url ?? ``}`;
    const editvideourl = `/edit/${channel}/${data?.url ?? ``}`;
    const views = data?.views ?? `${Math.floor(Math.random()*5+1)}k`;
    const likes = data?.likes ?? `${Math.floor(Math.random()*10)+1} jours`;
    const is_hidden = data?.is_hidden ?? `false`;
    let is_hidden_class = ``;
    if (is_hidden){is_hidden_class = " is_hidden"}

    let can_edit_video = false;
    let update_video_link = ``;
    if (typeof own_profile !== 'undefined') {
        if (own_profile) {
            can_edit_video = true;
        }
    }
    if (typeof authorized_to_edit_all_videos !== 'undefined') {
        if (authorized_to_edit_all_videos) {
            can_edit_video = true;
        }
    }
    if (can_edit_video)  {update_video_link=`<a class="editlink" href="${editvideourl}"><img class="editicon" src="/images/edit.svg" alt="Edit"></a>`;}

    const card = document.createElement('article');
        card.className = 'video-card';
        card.innerHTML = `
            <a class="thumbnaillink" href="${url}"><img class="thumbnail${is_hidden_class}" src="${thumb}" alt="Miniature ${i}">${has_already_been_seen_icon}</a>
            <div class="meta">
                <a class="avatar" aria-hidden="true" href="${channelurl}"><img class="pfp" src="/pfp_of/${channel}" alt="${channel} pfp"></a>
                <div class="info">
                    <div><a class="title" title="${title}" href="${url}">${title}</a></div>
                    <div><a class="sub" href="${channelurl}">${channel} • ${views} views • ${likes} likes${first_upload_date_text}</a></div>
                </div>
                ${is_youtube_video_icone}
                ${update_video_link}
                <div class="card-actions">
                    <button class="more-options" type="button"
                            aria-label="Video options" aria-expanded="false">
                        ⋮
                    </button>
                    <div class="card-menu" hidden>
                        <button type="button" data-action="add-to-playlist">Add to a playlist</button>
                        <button type="button" data-action="add-to-queue">Add to queue</button>
                        <button type="button" data-action="mark-as-seen">Set as already seen</button>
                        <button type="button" data-action="share">Share</button>
                    </div>
                </div>
            </div>
        `;
    card.dataset.videoId = data?.url ?? '';
    card.dataset.videoTitle = title;
    card.dataset.videoChannel = channel;
    return card;
}

const grid = document.createElement('div');
grid.className = 'video-grid';
gridcontent.appendChild(grid);


// Playlist manager window
async function addPlaylist(video) {
    await fetch("/api/playlists_api", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `playlist_action=add_playlist`
        })
        .then(async response => {
            if (!response.ok) {
                // In case error (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // const data = await response.json();

            OpenWindowAddVideoToPlaylist(video);
            
        })
        .catch(error => {
            console.error("Detailed error:", error);
        });
}

async function onPlaylistCheckboxChange(video, playlist, is_in_playlist) {
    await fetch("/api/playlists_api", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `playlist_action=toggle_video_to_playlist&playlist_name=${playlist.name}&video_id=${video.id}&toggle_value=${is_in_playlist}`
        })
        .then(async response => {
            if (!response.ok) {
                // In case error (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            
        })
        .catch(error => {
            console.error("Detailed error:", error);
        });
}

function showPlaylistWindowManager(playlist_list, video) {
    document.getElementById('playlist-window-overlay')?.remove();

    const overlay = document.createElement('div');
    overlay.id = 'playlist-window-overlay';
    overlay.className = 'playlist-window-overlay';

    const dialog = document.createElement('section');
    dialog.className = 'playlist-window';
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    dialog.setAttribute('aria-labelledby', 'playlist-window-title');

    const header = document.createElement('header');
    header.className = 'playlist-window-header';

    const title = document.createElement('h2');
    title.id = 'playlist-window-title';
    title.textContent = 'Playlists';

    const actions = document.createElement('div');
    actions.className = 'playlist-window-actions';

    const addButton = document.createElement('button');
    addButton.className = 'playlist-window-button';
    addButton.type = 'button';
    addButton.textContent = '+';
    addButton.setAttribute('aria-label', 'Add a playlist');
    addButton.addEventListener('click', () => addPlaylist(video));

    const closeButton = document.createElement('button');
    closeButton.className = 'playlist-window-button';
    closeButton.type = 'button';
    closeButton.textContent = '×';
    closeButton.setAttribute('aria-label', 'Close playlist window');

    const closeWindow = () => {
        overlay.remove();
        document.removeEventListener('keydown', closeOnEscape);
    };
    const closeOnEscape = (event) => {
        if (event.key === 'Escape') closeWindow();
    };
    closeButton.addEventListener('click', closeWindow);
    document.addEventListener('keydown', closeOnEscape);

    actions.append(addButton, closeButton);
    header.append(title, actions);

    const list = document.createElement('ul');
    list.className = 'playlist-window-list';
    list.id = 'playlist-window-list';

    if (playlist_list.length === 0) {
        const emptyMessage = document.createElement('li');
        emptyMessage.className = 'playlist-window-empty';
        emptyMessage.textContent = 'No playlists';
        list.appendChild(emptyMessage);
    } else {
        for (const playlist of playlist_list) {
            const item = document.createElement('li');
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            const playlistName = document.createElement('span');

            checkbox.type = 'checkbox';
            checkbox.checked = playlist.is_in_playlsit;
            checkbox.addEventListener('change', () => {
                onPlaylistCheckboxChange(video, playlist, checkbox.checked);
            });
            playlistName.textContent = playlist.name;

            label.append(checkbox, playlistName);
            item.appendChild(label);
            list.appendChild(item);
        }
    }

    dialog.append(header, list);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    closeButton.focus();
}

// ---- Show or hide video option menu
function closeCardMenus() {
    for (const menu of grid.querySelectorAll('.card-menu')) {
        menu.hidden = true;
        menu.parentElement.querySelector('.more-options')?.setAttribute('aria-expanded', 'false');
    }
}

async function OpenWindowAddVideoToPlaylist(video) {

    await fetch("/api/playlists_api", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `playlist_action=get_playlist_list_and_video_presence&video_id=${video.id}`
        })
        .then(async response => {
            if (!response.ok) {
                // In case error (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            // Si tout va bien,
            const data = await response.json();
            showPlaylistWindowManager(data, video);
        })
        .catch(error => {
            alert(error);
            console.error("Detailed error:", error);
        });

}

function addVideoToQueue(video) {
    console.info('TODO: ajouter la vidéo à la file d’attente.', video);
}

function markVideoAsSeen(video) {
    console.info('TODO: marquer la vidéo comme déjà vue.', video);
}

function shareVideo(video) {
    console.info('TODO: partager la vidéo.', video);
}

const cardMenuActions = {
    'add-to-playlist': OpenWindowAddVideoToPlaylist,
    'add-to-queue': addVideoToQueue,
    'mark-as-seen': markVideoAsSeen,
    share: shareVideo
};

document.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    const actionButton = target.closest('.card-menu [data-action]');
    if (actionButton && grid.contains(actionButton)) {
        const card = actionButton.closest('.video-card');
        const action = cardMenuActions[actionButton.dataset.action];
        if (card && action) {
            action({
                id: card.dataset.videoId,
                title: card.dataset.videoTitle,
                channel: card.dataset.videoChannel
            });
        }
        closeCardMenus();
        return;
    }

    const optionsButton = target.closest('.more-options');
    if (!optionsButton || !grid.contains(optionsButton)) {
        closeCardMenus();
        return;
    }

    const actions = optionsButton.closest('.card-actions');
    const menu = actions?.querySelector('.card-menu');
    if (!menu) return;

    const shouldOpen = menu.hidden;
    closeCardMenus();
    menu.hidden = !shouldOpen;
    optionsButton.setAttribute('aria-expanded', String(shouldOpen));
});

document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;

    const openMenu = grid.querySelector('.card-menu:not([hidden])');
    if (!openMenu) return;

    const optionsButton = openMenu.parentElement.querySelector('.more-options');
    closeCardMenus();
    optionsButton?.focus();
});


// Créer N cartes d'exemple
loadFromServer()


// sentinel pour déclencher le chargement quand on arrive en bas
const sentinel = document.createElement('div');
sentinel.className = 'sentinel';
sentinel.style.height = '1px';
gridcontent.appendChild(sentinel);

// IntersectionObserver pour charger quand le sentinel est visible
observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
        loadFromServer()
    }
}, {
    root: null,
    rootMargin: '400px', // pré-charge avant d'atteindre le bas
    threshold: 0
});

observer.observe(sentinel);
