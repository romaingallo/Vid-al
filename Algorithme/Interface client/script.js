
// Génère des cartes d'exemple dans #gridcontent
const gridcontent = document.getElementById('gridcontent');
if (!gridcontent) throw new Error('Element #gridcontent introuvable');

// const params = new URLSearchParams(window.location.search);
// const channelId = params.get('channel');

async function loadFromServer() {
    try {
        let url = '/api/videos';
        if (typeof channel_name !== 'undefined') {
            url = `/api/channel/${channel_name}`;
        }
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json(); // attendre un tableau d'objets vidéo
        // data.forEach((v, i) => {
        //     const card = createCard(i + 1, v);
        //     grid.appendChild(card);
        // });
        for (const [i, v] of data.entries()) {
            const card = await createCard(i + 1, v);
            grid.appendChild(card);
        }
        return data;
    } catch (err) {
        console.error('Échec de chargement des vidéos:', err);
    }
}

async function loadTitleFromHost(videoId) {
    try {
        const res = await fetch(`http://localhost:5002/meta/${videoId}`); // changer l'URL si besoin
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        return `${data.title}`;
    } catch (err) {
        console.error('Échec de chargement des metadonnées:', err);
    }
}


const thumbPath = './images/miniatures/miniature0.jpg';
async function createCard(i, data = null) {
    const url = `/watch/${data?.url ?? ``}`;
    const title = await loadTitleFromHost(data?.url) ?? `Erreur de titre`;
    const channel = data?.channel ?? 'Chaîne';
    const channelurl = `/visit_channel/${channel}`;
    const views = data?.views ?? `${Math.floor(Math.random()*5+1)}k`;
    const likes = data?.likes ?? `${Math.floor(Math.random()*10)+1} jours`;
    const thumb = `http://localhost:5002/thumbnail/${data?.url}`;

    const card = document.createElement('article');
        card.className = 'video-card';
        card.innerHTML = `
            <a class="thumbnaillink" href="${url}"><img class="thumbnail" src="${thumb}" alt="Miniature ${i}"></a>
            <div class="meta">
                <a class="avatar" aria-hidden="true" href="${channelurl}"><img class="pfp" src="/pfp_of/${channel}" alt="${channel} pfp"></a>
                <div class="info">
                    <div><a class="title" href="${url}">${title}</a></div>
                    <div><a class="sub" href="${channelurl}">${channel} • ${views} vues • ${likes} likes</a></div>
                </div>
            </div>
        `;
    return card;
}

const grid = document.createElement('div');
grid.className = 'video-grid';
gridcontent.appendChild(grid);

// Créer N cartes d'exemple
const N = 6;
for (let i = 1; i <= N; i++) {
    loadFromServer()
}


// sentinel pour déclencher le chargement quand on arrive en bas
const sentinel = document.createElement('div');
sentinel.className = 'sentinel';
sentinel.style.height = '1px';
gridcontent.appendChild(sentinel);

// IntersectionObserver pour charger quand le sentinel est visible
const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
        for (let i = 1; i <= N; i++) {
            loadFromServer()
        }
    }
}, {
    root: null,
    rootMargin: '400px', // pré-charge avant d'atteindre le bas
    threshold: 0
});

observer.observe(sentinel);
