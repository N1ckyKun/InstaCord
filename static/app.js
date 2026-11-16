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

async function followUser(userid) {
    const button = document.getElementById(`button${userid}`);
    const count = document.getElementById(`count${userid}`);
    const response = await fetch(`/follow/${userid}`,{
        method: 'POST'
    });
    if(response.ok) {
        const data = await response.json();
        count.textContent =  `${data.count} Followers`;
        button.textContent = `${data.followed ? 'Following' : 'Follow User'}`;
    }
}

async function postComment(postid) {
    const input = document.getElementById(`input${postid}`);
    const response = await fetch(`/comment/${postid}`,{
        method: 'POST',
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ comment: input.value.trim() })
    });
    if(response.ok) {
        window.location.reload();
    }
}

async function togglePost(postid) {
    const bview = document.getElementById(`BView${postid}`);
    const bcomm = document.getElementById(`BComm${postid}`);
    const view = document.getElementById(`View${postid}`);
    const comm = document.getElementById(`Comm${postid}`);
    if (comm.style.display == "flex") {
            comm.style.display = "none";
            bcomm.style.backgroundColor = '#111111';
    }
    else {
        comm.style.display = "flex";
        bcomm.style.backgroundColor = '#222222';
        view.style.display = "none";
        bview.style.backgroundColor = '#111111';
    }
}

async function toggleView(postid) {
    const bview = document.getElementById(`BView${postid}`);
    const bcomm = document.getElementById(`BComm${postid}`);
    const view = document.getElementById(`View${postid}`);
    const comm = document.getElementById(`Comm${postid}`);
    if (view.style.display == "flex") {
        view.style.display = "none";
        bview.style.backgroundColor = '#111111';
    }
    else {
        view.style.display = "flex";
        bview.style.backgroundColor = '#222222';
        comm.style.display = "none";
        bcomm.style.backgroundColor = '#111111';
    }
}

async function deleteUser(userid) {
    const user = document.getElementById(`user${userid}`);
    const response = await fetch(`/deleteuser/${userid}`,{
        method: 'POST'
    });
    if (response.ok) {
        user.remove();
    }
}

async function adminUser(userid) {
    const button = document.getElementById(`admin${userid}`);
    const tag = document.getElementById(`tag${userid}`);
    const response = await fetch(`/adminuser/${userid}`,{
        method: 'POST'
    });
    if (response.ok) {
        const data = await response.json();
        button.textContent = `${data.admin ? 'Unadmin' : 'Admin'}`;
        tag.style.backgroundColor = data.color;
        tag.textContent = data.name;
    }
}