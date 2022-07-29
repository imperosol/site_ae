function get_club_id() {
    // L'url de cette page est de la forme /vie-etu/club/<club_id>/<club_name>
    // On récupère donc l'id du club à partir de l'url
    const url = document.location.href.split('/');
    return url[url.length - 2];
}

function reset_intern_nav_listeners() {
    const categories = ["members", "description"];
    for (const category of categories) {
        const id = "intern-nav-" + category;
        const button = document.getElementById(id);
        const func = window["show_" + category];
        if (button !== undefined && func !== undefined) {
            if (button.classList.contains("active")) {
                button.removeEventListener("click", func);
            } else {
                button.addEventListener("click", func);
            }
        }
    }
}


function unselect_buttons() {
    const nav_buttons = document.getElementById("intern-navigation").querySelectorAll(".nav-button");
    for (const button of nav_buttons) {
        button.classList.remove("active");
    }
}


/**
 * Crée le contenu HTML pour la liste des membres du club.
 * à partir de la réponse JSON de la requête /vie-etu/club/api/get-club-members/<club_id> sur l'API
 * @param json
 * @returns {void}
 */
function create_members_html(json) {
    const template = document.getElementById("members-template");
    let user_list = document.createElement("div");
    let president = document.createElement("div");
    let bureau = document.createElement("div");
    let members = document.createElement("div");
    president.innerHTML = "<h2>Président</h2><div class='member-group'></div>";
    bureau.innerHTML = "<h2>Bureau</h2><div class='member-group'></div>";
    members.innerHTML = "<h2>Membres</h2><div class='member-group'></div>";
    for (const member of json) {
        let member_html = document.importNode(template.content, true);
        const img = member_html.querySelector("img");
        img.src = '/static/img/club_logos/387677886267523113.png';
        img.alt = 'Photo de profil de ' + member.name;
        member_html.querySelector("h4").innerText = member.name;
        if (member.poste !== undefined) {
            member_html.querySelector("p").innerText = member.poste;
        }
        if (member.is_president) president.querySelector('.member-group').appendChild(member_html);
        else if (member.is_in_bureau) bureau.querySelector('.member-group').appendChild(member_html);
        else members.querySelector('.member-group').appendChild(member_html);
    }
    user_list.appendChild(president);
    user_list.appendChild(bureau);
    user_list.appendChild(members);
    document.getElementById("members").innerHTML = user_list.innerHTML;
}


/**
 * Affiche la liste des membres du club, change le bouton qui est actif
 * et réinitialise les listeners des boutons.
 * @returns {Promise<void>}
 */
async function show_members() {
    /* On réalise ici une évaluation paresseuse du contenu de la sous-page
    * d'affichage des membres.
    * Si son contenu est vide, alors on effectue un appel sur l'API pour construire la page.
    * Si le contenu n'est pas vide, ça signifie que celui-ci a déjà été construit puis a été
    * caché au cours de la navigation. Il suffit donc de changer son style.
    *
    * De cette manière, on limite la quantité de travail fournie par le serveur lors du chargement
    * initial de la page. */
    const club_id = get_club_id();
    unselect_buttons();
    document.getElementById("intern-nav-members").classList.add("active");
    document.getElementById("description").style.display = "none";
    document.querySelector("h1").innerText = "Membres du club";
    const members_div = document.getElementById("members");
    reset_intern_nav_listeners();
    if (members_div.children.length > 0) {
        members_div.style.display = "block";
        return;
    }
    const url = '/vie-etu/club/api/get-club-members/' + club_id;
    let members = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => {
        return res.json()
    });
    create_members_html(members);
}

/**
 * Affiche la description du club, change le bouton qui est actif
 * et réinitialise les listeners des boutons.
 * @returns {Promise<void>}
 */
async function show_description() {
    const club_id = get_club_id();
    unselect_buttons();
    document.getElementById("intern-nav-description").classList.add("active");
    reset_intern_nav_listeners();
    document.getElementById("members").style.display = "none";
    document.getElementById("description").style.display = "block";
    document.querySelector("h1").innerText = "Détail du club";
}

document.addEventListener("DOMContentLoaded", reset_intern_nav_listeners);
