function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');


/**
 * Fait grandir la zone de texte pour permettre à l'utilisateur de saisir son commentaire
 * @param element
 */
function auto_grow(element) {
    element.style.height = "0px";
    element.style.height = (element.scrollHeight) + "px";
}

function delete_annal(annal_id, element_id) {
    fetch(`/pedagogy/api/annal/${annal_id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        }
    }).then(response => {
        if (response.ok) {
            document.getElementById(element_id).remove();
        }
    }).catch(error => {
            console.log(error);
        }
    );
}

function approve_annal(annal_id, element_id) {
    fetch(`/pedagogy/api/annal/${annal_id}/approve/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        }
    }).then(response => {
        if (response.ok) {
            const annal = document.getElementById(element_id);
            annal.classList.remove('pending');
            annal.classList.add('approved');
            annal.querySelector(".moderator-menu").querySelector(".fa-check-circle").remove();
        }
    }).catch(error => {console.log(error);});
}

function toggle_user_review() {
    const content = document.getElementById('user-review').querySelector(".user-review-content");
    const chevron = document.getElementById("user-review-chevron");
    content.classList.toggle('shrink');
    chevron.toggleAttribute("fa-chevron-up");
    chevron.toggleAttribute("fa-chevron-down");
}

function put_review(html) {
    let new_node = document.createElement('div');
    new_node.innerHTML = html;
    new_node = new_node.firstElementChild;
    const review_id = new_node.id;
    let previous_review = document.getElementById(review_id);
    if (previous_review) {
        previous_review.innerHTML = new_node.innerHTML;
    } else {
        document.getElementById("user-review").insertAdjacentHTML('afterend', html);
    }
}

function validate_review(db_id, dom_id) {
    fetch(`/pedagogy/api/review/${db_id}/validate/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        }
    }).then(response => {
        if (response.ok) {
            const review = document.getElementById(dom_id);
            review.classList.remove('pending');
            review.classList.add('approved');
            review.querySelector(".moderator-menu").querySelector(".fa-check-circle").remove();
        } else {
            console.log(response.statusText)
        }
    })
}

function delete_review(db_id, dom_id) {
    fetch(`/pedagogy/api/review/${db_id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        }
    }).then(response => {
        if (response.ok) {
            document.getElementById(dom_id).remove();
        }
    });
}

function post_review() {
    const form = document.forms['post-review'];
    const form_data = new FormData(form);
    const req = new Request(form.action, {
        method: 'POST',
        body: form_data
    });
    fetch(req).then(response => {
        if (response.ok) {
            toggle_user_review();
            fetch(`/pedagogy/uvs/${form["uv"].value}/my-review/`, {
                method: 'GET',
            }).then(response => {
                if (response.ok) {
                    response.text().then(html => put_review(html));
                }
            });
        }
    });
}


function init() {
    const user_review = document.getElementById('user-review');
    user_review.querySelector('h4').addEventListener('click', toggle_user_review);
    const textarea = user_review.querySelector('textarea');
    textarea.addEventListener('keypress', () => auto_grow(textarea));

    document.getElementById('review-post-btn').addEventListener('click', post_review);
}

document.addEventListener('DOMContentLoaded', init);
