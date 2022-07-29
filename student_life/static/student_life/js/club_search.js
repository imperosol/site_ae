/**
 * Efface la section de recherche des clubs et repeuple son contenu avec la liste des clubs
 * passée en paramètre.
 *
 * @param clubs : JSON. Un objet JSON qui contient la liste des clubs à afficher,
 * sous la même forme que celle retournée par la requête sur l'API `vie-etu/club/api/get`
 * @returns {void}
 */
function display_clubs(clubs) {
    let dom_list = document.createDocumentFragment();
    for (const club of clubs) {
        let item = document.createElement('a');
        item.href = '/vie-etu/club/' + club.id + '/' + club.name.toLowerCase().replace(/\s/g, '');
        item.innerHTML = `
             <img src="/${club.logo}" alt="logo du club ${club.name}" width="50px" height="50px">
             <div class="description">
                 <h5>${club.name}</h5>
                 ${club.president !== null ? `<p class="president">Président :  ${club.president}</p>` : ''}
                 <p>${club.short_description}</p>
             </div>`;
        dom_list.appendChild(item);
        dom_list.appendChild(document.createElement('hr'));
    }
    document.getElementById('club-list').replaceChildren(dom_list);
}

function set_pagination_buttons(current_page) {
    const buttons = document.getElementById('club-pagination').querySelectorAll('button');
    for (const button of buttons) {
        button.disabled = (parseInt(button.value) === current_page);
    }
}

/**
 *
 * @returns {Array[Element]}
 */
function get_search_form_content() {
    const form = document.forms['filter-form'];
    let inputs = form.querySelectorAll('input[type="text"]');
    inputs = Array.from(inputs).filter(e => e.value.length > 0);
    const order_by = form.querySelector('select[name="order-by"]');
    const order_direction = form.querySelector('input[type="radio"][name="order-direction"]:checked');

    if (order_by.value !== '') {
        // On crée un nouvel élément de formulaire
        // pour pouvoir modifier son contenu sans modifier le formulaire original
        let order_by_input = document.createElement('input');
        order_by_input.type = 'hidden';
        order_by_input.name = 'order-by';
        if (order_direction.value === 'asc') {
            order_by_input.value = order_by.value;
        } else {
            order_by_input.value = '-' + order_by.value;
        }
        console.log(order_by_input);
        inputs = inputs.concat(order_by_input);
    }
    console.log(inputs);
    return inputs;
}

/**
 * @returns {void}
 */
async function club_search(page = 1) {
    const form_content = get_search_form_content();
    let get_request = form_content.reduce((acc, cur) => acc + cur.name + '=' + cur.value + '&', '');
    get_request += 'page=' + page + '&';
    const url = '/vie-etu/club/api/get?' + get_request;
    console.log(url);
    let res = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => {
        return res.json()
    });
    display_clubs(res);
    set_pagination_buttons(page);
}

function init_event_listeners() {
    for (const button of document.getElementById('club-pagination').querySelectorAll('button')) {
        const page = parseInt(button.value);
        button.addEventListener('click', () => club_search(page));
    }
    for (const form_field of document.forms['filter-form']) {
        form_field.addEventListener('keypress', e => {
            if (e.key === 'Enter') club_search()
        })
    }

    const validate_button = document.getElementById('search-form-validation');
    validate_button.addEventListener('click', () => club_search());
    validate_button.addEventListener('keypress', e => {
        if (e.key === 'Enter') club_search()
    });
}

document.addEventListener('DOMContentLoaded', init_event_listeners)