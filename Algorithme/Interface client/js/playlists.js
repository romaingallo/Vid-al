const storageKey = 'videal-playlists';
const listElement = document.getElementById('playlist-list');
const videosElement = document.getElementById('playlist-videos');
const nameInput = document.getElementById('selected-playlist-name');
const sortSelect = document.getElementById('playlist-sort-order');
const messageElement = document.getElementById('playlist-message');
let playlists = [];
let selectedPlaylistId = null;

function showMessage(message) {
    messageElement.textContent = message;
}

// function savePlaylists() {
//     try {
//         window.localStorage.setItem(storageKey, JSON.stringify(playlists));
//     } catch (error) {
//         console.error('Unable to save playlists in this browser.', error);
//         showMessage('Could not save changes in this browser.');
//     }
// }

// function makeVideo(title, channel, uploadDate, addedDate) {
//     return {
//         id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
//         title: title,
//         channel: channel,
//         uploadDate: uploadDate,
//         addedDate: addedDate,
//         thumbnail: '/images/miniatures/miniature0.jpg',
//         url: ''
//     };
// }

async function loadPlaylists() {
    // fetch and load the list of all user playlist
    await fetch("/api/playlists_api", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `playlist_action=get_all_playlists`
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
            playlists = data;
            // console.log(`Playlist list :`);
            // console.log(playlists);
        })
        .catch(error => {
            showMessage(error.message);
            console.error("Detailed error:", error);
        });
}

function selectedPlaylist() {
    return playlists.find(function (playlist) {
        return playlist.id === selectedPlaylistId;
    }) || null;
}

async function addPlaylist(name) {
    let playlist_name_form = '';
    if (name) playlist_name_form = `&new_playlist_name=${name}`
    await fetch("/api/playlists_api", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `playlist_action=add_playlist${playlist_name_form}`
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
            playlists = data;
            // console.log(`Playlist list :`);
            // console.log(playlists);
            render();
        })
        .catch(error => {
            showMessage(error.message);
            console.error("Detailed error:", error);
        });
}

async function deletePlaylist(name) {
    await fetch("/api/playlists_api", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `playlist_action=delete_playlist&playlist_name=${name}`
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
            playlists = data;
            showMessage(`Playlist '${name}' deleted`);
            render();
        })
        .catch(error => {
            showMessage(error.message);
            console.error("Detailed error:", error);
        });
}

async function updatePlaylistName(old_name, new_name) {
    await fetch("/api/playlists_api", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `playlist_action=update_playlist_name&old_playlist_name=${old_name}&new_playlist_name=${new_name}`
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
            playlists = data;
            showMessage(`Playlist '${old_name}' name set to '${new_name}'`);
            render();
        })
        .catch(error => {
            showMessage(error.message);
            console.error("Detailed error:", error);
        });
}


async function removeVideoFromPlaylist(video_url, playlist_name) {
    await fetch("/api/playlists_api", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `playlist_action=remove_video_from_playlist&video_id=${video_url}&playlist_name=${playlist_name}`
        })
        .then(async response => {
            if (!response.ok) {
                // In case error (ex: 400, 500)
                return response.json().then(err => {
                    throw new Error(err.error || "Unknown error.");
                });
            }
            
            showMessage(`Video '${video_url}' removed from '${playlist_name}'`);
        })
        .catch(error => {
            showMessage(error.message);
            console.error("Detailed error:", error);
        });
}

function createButton(label, className, onClick, title) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.textContent = label;
    if (title) button.title = title;
    button.addEventListener('click', onClick);
    return button;
}

function shuffle(items) {
    alert("Not implemented, yet.")
    // for (let index = items.length - 1; index > 0; index -= 1) {
    //     const swapIndex = Math.floor(Math.random() * (index + 1));
    //     [items[index], items[swapIndex]] = [items[swapIndex], items[index]];
    // }
    // return items;
}

function orderedVideos(playlist) {
    // alert("Not implemented, yet.")
    const videos = playlist.videos.slice();
    switch (playlist.sort) {
        case 'date-desc':
            return videos.sort((a, b) => b.uploadDate.localeCompare(a.uploadDate));
        case 'date-asc':
            return videos.sort((a, b) => a.uploadDate.localeCompare(b.uploadDate));
        case 'added-desc':
            return videos.sort((a, b) => b.addedDate.localeCompare(a.addedDate));
        case 'added-asc':
            return videos.sort((a, b) => a.addedDate.localeCompare(b.addedDate));
        case 'title-asc':
            return videos.sort((a, b) => a.title.localeCompare(b.title));
        case 'title-desc':
            return videos.sort((a, b) => b.title.localeCompare(a.title));
        case 'random':
            return videos;
        default:
            return videos;
    }
}

function renderPlaylists() {
    listElement.replaceChildren();
    playlists.forEach(function (playlist) {
        const button = createButton(
            playlist.name,
            'playlist-button',
            function () {
                selectedPlaylistId = playlist.id;
                showMessage('');
                render();
            }
        );
        button.setAttribute('aria-current', String(playlist.id === selectedPlaylistId));
        button.setAttribute('aria-label', `${playlist.name}, ${playlist.videos.length} videos`);

        const count = document.createElement('span');
        count.className = 'playlist-count';
        count.textContent = `(${playlist.videos.length} videos)`;
        button.appendChild(count);

        listElement.appendChild(button);

    });
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


async function renderVideos(playlist) {
    videosElement.replaceChildren();
    if (!playlist || playlist.videos.length === 0) {
        const emptyState = document.createElement('p');
        emptyState.className = 'empty-playlist';
        emptyState.textContent = playlist
        ? 'This playlist is empty.'
        : 'Create a playlist to get started.';
        videosElement.appendChild(emptyState);
        return;
    }
    
    const videos = playlist.sort === 'random'
    ? playlist.videos
    : orderedVideos(playlist);
    for (const [index, video] of videos.entries()) {
        const row = document.createElement('article');
        row.className = 'playlist-video-row'
        const card = document.createElement('a');
        card.className = 'playlist-video';

        const position = document.createElement('span');
        position.className = 'video-position';
        position.textContent = String(index + 1);
        position.setAttribute('aria-label', `Position ${index + 1}`);


        const is_youtube_video = video.is_youtube_video ?? `false`;
        let thumbnail_source = `${video.channel_url}/thumbnail/${video.videourl}`;
        let title_text = `Loading title ?`;
        const url = `/watch/${encodeURIComponent(video.videourl ?? ``)}?playlist=1`;
        let channel = video.author_name ?? 'Chaîne';
        let channelurl = `/visit_channel/${channel}`;
        const has_already_been_seen = video.already_seen ?? false;
        if (is_youtube_video == true) 
            {
                thumbnail_source = `https://i.ytimg.com/vi/${video.videourl}/hqdefault.jpg`;
                const data_from_youtube = await loadDataFromYoutube(video.videourl);
                title_text = data_from_youtube?.title ?? `Erreur de titre`;
                if (channel == 'UnknownFromYoutube')
                {
                    channel = data_from_youtube?.author_name ?? `Erreur de nom`;
                    channelurl = data_from_youtube?.author_url ?? ``;
                }
            }
        else
        {
            title_text = await loadTitleFromHost(video.videourl, video.channel_url) ?? `Erreur de titre`;
        }

        const thumbnail_div = document.createElement('div');
        thumbnail_div.className = 'video-thumbnail-wrapper';
        const thumbnail = document.createElement('img');
        thumbnail.className = 'video-thumbnail';
        if (video.is_hidden) thumbnail.className += ' is_hidden';
        thumbnail.src = thumbnail_source;
        thumbnail_div.append(thumbnail);
        if (has_already_been_seen)
        {
            const has_been_seen_icon = document.createElement('img');
            has_been_seen_icon.className = 'hasbeenseenicon';
            has_been_seen_icon.src = '/images/check_white.svg';
            has_been_seen_icon.alt = 'Has been seen';
            thumbnail_div.append(has_been_seen_icon);
        }

        const details = document.createElement('div');
        details.className = 'video-details';
        const title = document.createElement('a');
        title.className = 'video-title';
        title.textContent = title_text;
        title.href = url;
        if (!video.videourl) {
            title.addEventListener('click', function (event) {
                event.preventDefault();
            });
        }
        const meta = document.createElement('div');
        meta.className = 'video-meta';
        const pfp = document.createElement('a');
        pfp.className = 'avatar';
        pfp.href = channelurl;
        const pfp_image = document.createElement('img');
        pfp_image.className = 'pfp';
        pfp_image.src = `/pfp_of/${channel}`;
        pfp_image.alt = `${channel} pfp`
        pfp.append(pfp_image);
        const metaText = document.createElement('a');
        metaText.textContent = `${channel} · Uploaded ${video.first_upload} · Added ${video.date_added_in_playlist}`;
        metaText.href = channelurl;
        metaText.className = 'video-meta';
        meta.append(pfp, metaText);
        
        
        const stats = document.createElement('div');
        stats.className = 'video-stats';
        if (is_youtube_video == true) 
        {
            const is_from_youtube_icon = document.createElement('img');
            is_from_youtube_icon.className = 'isfromyoutubeicon';
            is_from_youtube_icon.src = '/images/favicon.ico';
            is_from_youtube_icon.alt = 'From Youtube';
            stats.append(is_from_youtube_icon);
        }
        const statsText = document.createElement('a');
        statsText.textContent = `${video.nb_likes} likes · ${video.nb_views} views`;
        statsText.href = url;
        statsText.className = 'video-stats';
        stats.append(statsText);
        

        details.append(title, meta, stats);

        const actions = document.createElement('div');
        actions.className = 'video-actions';
        const isManual = playlist.sort === 'manual';
        const moveUp = createButton('↑', 'move-button', function () {
            moveVideo(playlist, video.id, -1);
        }, 'Move video up');
        const moveDown = createButton('↓', 'move-button', function () {
            moveVideo(playlist, video.id, 1);
        }, 'Move video down');
        moveUp.disabled = !isManual || index === 0;
        moveDown.disabled = !isManual || index === videos.length - 1;
        actions.append(moveUp, moveDown, createButton('Remove', 'video-action', function () {
            removeVideoFromPlaylist(video.videourl, playlist.name).then(
                function () {
                    playlist.videos = playlist.videos.filter(function (item) {
                        return item.videourl !== video.videourl;
                    });
                    render();
                }
            )
            
        }));
        card.href = url;
        card.addEventListener('click', function (event) {
            const target = event.target;
            if (!(target instanceof Element)) return;
            const clickedLink = target.closest('a');
            if (clickedLink && clickedLink !== card && !clickedLink.href.startsWith(`${window.location.origin}/watch/`)) return;
            window.playlistPlayback.savePlaylist(playlist, videos, video.videourl);
        });
        card.append(position, thumbnail_div, details);
        row.append(card, actions);
        videosElement.appendChild(row);
    }
}

function moveVideo(playlist, videoId, direction) {
    alert("Not implemented, yet.")
    // if (playlist.sort !== 'manual') return;
    // const index = playlist.videos.findIndex(function (video) {
    //     return video.id === videoId;
    // });
    // const targetIndex = index + direction;
    // if (index < 0 || targetIndex < 0 || targetIndex >= playlist.videos.length) return;
    // [playlist.videos[index], playlist.videos[targetIndex]] =
    //     [playlist.videos[targetIndex], playlist.videos[index]];
    // // savePlaylists();
    // render();
}

async function render() {
    const playlist = selectedPlaylist();
    renderPlaylists();
    nameInput.value = playlist ? playlist.name : '';
    nameInput.disabled = !playlist;
    document.querySelector('#playlist-rename-form button').disabled = !playlist;
    document.getElementById('delete-playlist').disabled = !playlist;
    sortSelect.disabled = !playlist;
    sortSelect.value = playlist ? playlist.sort : 'manual'; // Playing order
    renderVideos(playlist);
}

document.getElementById('playlist-create-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const input = document.getElementById('new-playlist-name');
    const name = input.value.trim();
    addPlaylist(name);
    input.value = '';
    showMessage('');
});

document.getElementById('playlist-rename-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const playlist = selectedPlaylist();
    const newName = nameInput.value.trim();
    if (!playlist || !newName) {
        showMessage('Playlist names cannot be empty.');
        return;
    }
    updatePlaylistName(playlist.name, newName);
    // playlist.name = newName;
});

document.getElementById('delete-playlist').addEventListener('click', function () {
    const playlist = selectedPlaylist();
    if (!playlist || !window.confirm(`Delete "${playlist.name}"?`)) return;
    deletePlaylist(playlist.name)
    selectedPlaylistId = playlists.length ? playlists[0].id : null;
});

sortSelect.addEventListener('change', function () {
    const playlist = selectedPlaylist();
    if (!playlist) return;
    playlist.sort = sortSelect.value;
    if (playlist.sort === 'random') shuffle(playlist.videos);
    // savePlaylists();
    render();
});

loadPlaylists().then(render);
// selectedPlaylistId = playlists.length ? playlists[0].id : null;
// render();