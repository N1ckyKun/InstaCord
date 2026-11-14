async function updateLike(postid) {
    const button = document.getElementById(postid);
    const response = await fetch(`/like/${postid}`,{
        method: 'POST'
    });
    if(response.ok) {
        const data = await response.json();
        button.textContent = `${data.liked ? '❤️' : '🤍'} ${data.count}`;
    }
}

async function deletePost(postid) {
    const post = document.getElementById(`post${postid}`);
    const response = await fetch(`/delete/${postid}`,{
        method: 'POST'
    });
    if (response.ok) {
        post.remove();
    }
}