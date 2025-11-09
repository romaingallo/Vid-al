const likeBtn = document.getElementById('btn-like');
const dislikeBtn = document.getElementById('btn-dislike');
const likeCount = document.getElementById('like-count');
const dislikeCount = document.getElementById('dislike-count');

function getCSRF() {
    const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/);
    if (match) return decodeURIComponent(match[1]);
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : null;
}

async function request(action){
    // Envoi requete
    const headers = {'Content-Type': 'application/json'};
    const csrf = getCSRF();
    if (csrf) headers['X-CSRFToken'] = csrf;
    const res = await fetch(`/api/videos/${videoId}/react`, {
        method: 'POST',
        credentials: 'same-origin',
        headers,
        body: JSON.stringify({action})
    });
    if (!res.ok) {
        console.error('Reaction failed', await res.text());
        return;
    }
    else {
        return res.json();
    }
}

async function react(action){
    // 
    const data = await request(action);
    likeCount.textContent = data.likes;
    dislikeCount.textContent = data.dislikes;
    // likeBtn.classList.toggle('active', data.user_reaction === 'like');
    // dislikeBtn.classList.toggle('active', data.user_reaction === 'dislike');
    // likeBtn.setAttribute('aria-pressed', data.user_reaction === 'like');
    // dislikeBtn.setAttribute('aria-pressed', data.user_reaction === 'dislike');
}

// async function initReaction(){
//     const initdata = await request('get');
//     // console.log(initdata);
//     likeCount.textContent = initdata.likes;
//     dislikeCount.textContent = initdata.dislikes;
// }
// initReaction();

likeBtn.addEventListener('click', () => react('like'));
dislikeBtn.addEventListener('click', () => react('dislike'));
