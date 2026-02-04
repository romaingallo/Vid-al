// Source vidéo
const videoElement = document.getElementById('video');
if (!videoElement) throw new Error('Element #videoElement introuvable');

// const params = new URLSearchParams(window.location.search);
// const videoId = params.get('video');

let hls_url = '';
let dash_url = '';

if (videoId !== '') {
    hls_url = `${hostURLSource}/video/${videoId}/playlist.m3u8`
    dash_url = `${hostURLSource}/video/${videoId}/manifest.mpd`
    // const sourceElement = document.createElement('source');
    // sourceElement.src = dash_url;
    // sourceElement.type = 'application/dash+xml';
    // videoElement.appendChild(sourceElement);
} else {
    console.warn('Aucun paramètre video dans l\'URL');
}

// Titre, decription, ...


const titleElement = document.getElementById('title');
const descriptionElement = document.getElementById('description');
if (!titleElement) throw new Error('Element #titleElement introuvable');
if (!descriptionElement) throw new Error('Element #descriptionElement introuvable');

async function loadMetadataFromServer() {
    try {
        const res = await fetch(`${hostURLSource}/meta/${videoId}`); // changer l'URL si besoin
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json(); // attendre un tableau d'objets vidéo
        titleElement.textContent = data.title;
        descriptionElement.textContent = data.descritpion;
        return data;
    } catch (err) {
        console.error('Échec de chargement des metadonnées:', err);
    }
}

loadMetadataFromServer()


document.addEventListener('DOMContentLoaded', function() {
            var player = videojs('video', {
                techOrder: ["html5"],
                sources: [
                    {
                        src: dash_url,
                        type: "application/dash+xml"
                    }
                ]
            });

            player.on('error', function() {
                console.log('Video player error:', player.error());
            });
        });
