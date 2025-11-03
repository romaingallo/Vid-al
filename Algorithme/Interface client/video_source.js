// Source vidéo
const videoElement = document.getElementById('video');
if (!videoElement) throw new Error('Element #videoElement introuvable');

const params = new URLSearchParams(window.location.search);
const videoId = params.get('video');

if (videoId) {
    const sourceElement = document.createElement('source');
    sourceElement.src = `http://localhost:5002/video/${videoId}`;
    sourceElement.type = 'video/mp4';
    videoElement.appendChild(sourceElement);
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
        const res = await fetch(`http://localhost:5002/meta/${videoId}`); // changer l'URL si besoin
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
