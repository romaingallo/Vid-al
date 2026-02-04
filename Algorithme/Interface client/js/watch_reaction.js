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
    likeBtn.classList.toggle('green0', false);
    dislikeBtn.classList.toggle('red0', false);
    likeBtn.classList.toggle('green100', false);
    dislikeBtn.classList.toggle('red100', false);
    likeBtn.classList.toggle('green50', action == 'like');
    dislikeBtn.classList.toggle('red50', action == 'dislike');
    const data = await request(action);

    likeCount.textContent = data.likes;
    dislikeCount.textContent = data.dislikes;
    likeBtn.classList.toggle('green50', false);
    dislikeBtn.classList.toggle('red50', false);
    likeBtn.classList.toggle('green100', data.personal_like_result == 'like');
    dislikeBtn.classList.toggle('red100', data.personal_like_result == 'dislike');
    likeBtn.classList.toggle('green0', data.personal_like_result != 'like');
    dislikeBtn.classList.toggle('red0', data.personal_like_result != 'dislike');

}

likeBtn.addEventListener('click', () => react('like'));
dislikeBtn.addEventListener('click', () => react('dislike'));
