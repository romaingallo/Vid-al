const titleElement = document.getElementById('title');
if (!titleElement) throw new Error('Element #titleElement introuvable');
const channel_linkElement = document.getElementById('channel_link');
if (!channel_linkElement) throw new Error('Element #channel_linkElement introuvable');
const pfpElement = document.getElementById('pfp');
if (!pfpElement) throw new Error('Element #pfpElement introuvable');
const subElement = document.getElementById('sub');
if (!subElement) throw new Error('Element #subElement introuvable');

async function loadDataFromYoutube(video_id) {
    try {
        const res = await fetch(`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${video_id}&format=json`); // changer l'URL si besoin
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        return data;
    } catch (err) {
        console.error('Échec de chargement des metadonnées:', err);
    }
}

async function showMetadata() {
    if (videoId !== '') {

        const data_from_youtube = await loadDataFromYoutube(videoId);
        const title = data_from_youtube?.title ?? `Erreur de titre`;
        const channel = data_from_youtube?.author_name ?? `Erreur de nom`;
        const channelurl = data_from_youtube?.author_url ?? ``;

        titleElement.innerText = title;
        channel_linkElement.href = channelurl;
        pfpElement.src = `/pfp_of/${channel}`;
        pfpElement.alt = `${channel} pfp`;
        subElement.src = channelurl;
        subElement.innerText = `${channel} • xxx vues • xxx jours`;

    } else {
        console.warn('Aucun paramètre video dans l\'URL');
    }
}

showMetadata()