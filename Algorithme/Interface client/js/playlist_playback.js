(function () {
    const storageKey = 'videal-current-playlist';
    const playlistPanel = document.getElementById('playlistpanel');
    const playlistList = document.getElementById('watch-playlist-list');
    const currentVideoId = document.getElementById('contentwatch')?.dataset.videoId;

    function videoIdOf(video) {
        return String(video.videourl ?? video.id ?? '');
    }

    function savePlaylist(playlist, videos, selectedVideoId) {
        const savedVideos = videos
            .map(function (video) {
                const id = videoIdOf(video);
                if (!id) return null;
                return {
                    id: id,
                    title: video.title ?? '',
                    is_youtube_video: video.is_youtube_video === true || video.is_youtube_video === 'true',
                    channel_url: video.channel_url ?? '',
                    author_name: video.author_name ?? '',
                    is_hidden: video.is_hidden === true
                };
            })
            .filter(Boolean);

        const selectedId = String(selectedVideoId ?? '');
        if (!savedVideos.length || !savedVideos.some(function (video) { return video.id === selectedId; })) return false;

        try {
            window.localStorage.setItem(storageKey, JSON.stringify({
                playlistId: playlist.id,
                playlistName: playlist.name,
                videos: savedVideos,
                currentVideoId: selectedId
            }));
            return true;
        } catch (error) {
            console.error('Unable to save the current playlist in this browser.', error);
            return false;
        }
    }

    function loadPlaylist() {
        if (new URLSearchParams(window.location.search).get('playlist') !== '1') return null;

        try {
            const savedPlaylist = window.localStorage.getItem(storageKey);
            if (!savedPlaylist) return null;

            const playlist = JSON.parse(savedPlaylist);
            if (!playlist || !Array.isArray(playlist.videos) ||
                !playlist.videos.every(function (video) {
                    return video && typeof video.id === 'string';
                })) {
                throw new Error('Saved playlist has an invalid format.');
            }
            return playlist;
        } catch (error) {
            console.error('Unable to load the current playlist from this browser.', error);
            return null;
        }
    }

    function saveCurrentVideo(id) {
        const playlist = loadPlaylist();
        if (!playlist || !playlist.videos.some(function (video) { return video.id === id; })) return;

        playlist.currentVideoId = id;
        try {
            window.localStorage.setItem(storageKey, JSON.stringify(playlist));
        } catch (error) {
            console.error('Unable to update the current video in the saved playlist.', error);
        }
    }

    async function loadVideoMetadata(video) {
        const isYoutubeVideo = video.is_youtube_video === true || video.is_youtube_video === 'true';
        const url = isYoutubeVideo
            ? `https://www.youtube.com/oembed?url=${encodeURIComponent(`https://www.youtube.com/watch?v=${video.id}`)}&format=json`
            : `${video.channel_url}/meta/${encodeURIComponent(video.id)}`;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`Unable to load metadata for video ${video.id}.`, error);
            return null;
        }
    }

    function renderPlaylist() {
        if (!playlistPanel || !playlistList || !currentVideoId) return;

        const playlist = loadPlaylist();
        const activeVideo = playlist?.videos.find(function (video) {
            return video.id === currentVideoId;
        });
        if (!playlist || !activeVideo) {
            playlistPanel.hidden = true;
            return;
        }

        playlistPanel.hidden = false;
        const heading = document.getElementById('playlist-panel-title');
        if (heading) heading.textContent = playlist.playlistName || 'Playlist';
        playlistList.replaceChildren();

        playlist.videos.forEach(function (video) {
            const item = document.createElement('li');
            item.className = 'watch-playlist-item';
            if (video.id === currentVideoId) {
                item.classList.add('is-active');
                item.setAttribute('aria-current', 'true');
            }

            const link = document.createElement('a');
            link.className = 'watch-playlist-link';
            link.dataset.videoId = video.id;
            link.href = `/watch/${encodeURIComponent(video.id)}?playlist=1`;
            link.addEventListener('click', function () {
                saveCurrentVideo(video.id);
            });

            const thumbnail = document.createElement('img');
            thumbnail.className = 'watch-playlist-thumbnail';
            thumbnail.alt = '';
            thumbnail.src = video.is_youtube_video
                ? `https://img.youtube.com/vi/${encodeURIComponent(video.id)}/hqdefault.jpg`
                : `${video.channel_url}/thumbnail/${encodeURIComponent(video.id)}`;

            const details = document.createElement('div');
            details.className = 'watch-playlist-details';
            const title = document.createElement('span');
            title.className = 'watch-playlist-video-title';
            title.textContent = video.title || 'Loading title…';

            const author = document.createElement('span');
            author.className = 'watch-playlist-author';
            const avatar = document.createElement('img');
            avatar.src = `/pfp_of/${encodeURIComponent(video.author_name || '')}`;
            avatar.alt = '';
            const authorName = document.createElement('span');
            authorName.textContent = video.author_name || 'Unknown channel';
            author.append(avatar, authorName);
            details.append(title, author);
            link.append(thumbnail, details);
            item.appendChild(link);
            playlistList.appendChild(item);

            loadVideoMetadata(video).then(function (metadata) {
                if (!metadata) {
                    title.textContent = video.title || 'Title unavailable';
                    return;
                }
                title.textContent = video.title || metadata.title || 'Title unavailable';
                if (video.author_name === 'UnknownFromYoutube' && metadata.author_name) {
                    authorName.textContent = metadata.author_name;
                    avatar.src = `/pfp_of/${encodeURIComponent(metadata.author_name)}`;
                }
            });
        });
    }

    window.playlistPlayback = {
        savePlaylist: savePlaylist
    };

    renderPlaylist();
})();
