/**
 * Fait grandir la zone de texte pour permettre à l'utilisateur de saisir son commentaire
 * @param element
 */
function auto_grow(element) {
    element.style.height = "0px";
    element.style.height = (element.scrollHeight)+"px";
}

function show_user_comment() {
    const content = document.getElementById('user-review').querySelector(".user-review-content");
    const chevron = document.getElementById("user-review-chevron");
    content.classList.toggle('shrink');
    chevron.toggleAttribute("fa-chevron-up");
    chevron.toggleAttribute("fa-chevron-down");
}


function init() {
    const user_review = document.getElementById('user-review');
    user_review.querySelector('h4').addEventListener('click', show_user_comment);
    const textarea = user_review.querySelector('textarea');
    textarea.addEventListener('keypress', () => auto_grow(textarea));
}

document.addEventListener('DOMContentLoaded', init);
