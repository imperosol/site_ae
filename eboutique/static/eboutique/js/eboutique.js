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


function confirm_item_input_count(product_id) {
    let new_nb_item = parseInt(document.getElementById(product_id).querySelector('input').value);
    if (new_nb_item > 0) {
        basket[product_id] = new_nb_item;
        edit_money_slot(document.getElementById(product_id), product_id);
    } else {
        document.getElementById(product_id).remove();
        delete basket[product_id];
    }
    update_balance();
}


function make_count_editable(product_id) {
    let count_elem = document.getElementById(product_id).querySelector('.count-value');
    count_elem.innerHTML = '<input type="number" value="' + basket[product_id] + '" />';
    let new_input = count_elem.querySelector('input');
    new_input.focus();
    new_input.value = '';  // astuce pour placer le curseur à la fin
    new_input.value = basket[product_id];
    new_input.select();

    new_input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            confirm_item_input_count(product_id);
        }
    });
}


function get_product_id(button) {
    let id = null;
    if (button.classList.contains('item')) {
        id = button.id.split('-')[1];
    } else if (button.parentElement.classList.contains('item-count')) {
        id = button.parentElement;
    }
    return parseInt(id) ? id : null;
}

function create_money_slot(product_id) {
    const money_panel = document.getElementById('money-panel-content');
    const template = document.getElementById('money-slot-template');
    let money_slot = document.createElement('div');
    money_slot.appendChild(template.content.cloneNode(true));

    const price = (products[product_id]['price'] / 100).toFixed(2);
    const descr = products[product_id]['name'];
    money_slot.id = product_id;
    money_slot.className = 'money-slot';
    money_slot.querySelector('.money-descr').innerHTML = descr;
    money_slot.querySelector('.money-amount').innerHTML = price + " €";

    money_slot.querySelector('.plus').addEventListener('click', () => add_item(product_id));
    money_slot.querySelector('.minus').addEventListener('click', () => remove_item(product_id));
    money_slot.querySelector('.count-value').addEventListener('dblclick', () => make_count_editable(product_id));

    money_panel.appendChild(money_slot);
}

function create_combination_slot(combination_id) {
    const money_panel = document.getElementById('money-panel-content');
    const template = document.getElementById('money-slot-template');
    let combination_slot = document.createElement('div');
    combination_slot.appendChild(template.content.cloneNode(true));

    const price = (combinations[combination_id]['price'] / 100).toFixed(2);
    const descr = combinations[combination_id]['name'];
    const str_id = `comb-${combination_id}`;
    combination_slot.id = str_id;
    combination_slot.className = 'money-slot';
    combination_slot.querySelector('.money-descr').innerHTML = descr;
    combination_slot.querySelector('.money-amount').innerHTML = price + " €";

    const secondary_slot = document.createElement('div');
    secondary_slot.className = 'secondary-slot';
    let comb_items = [];
    for (const product of combinations[combination_id]['products']) {
        comb_items.push(products[product]['name']);
    }
    secondary_slot.innerHTML = `<h3 class="money-descr">${comb_items.join(' - ')}</h3>`;
    combination_slot.appendChild(secondary_slot);

    combination_slot.querySelector('.plus').addEventListener('click', () => {
        basket[str_id]++;
        edit_combination_slot(combination_slot, str_id);
        update_balance();
    });
    combination_slot.querySelector('.minus')
        .addEventListener('click', () => {
            if (basket[str_id] > 1) {
                basket[str_id]--;
                edit_combination_slot(combination_slot, str_id);
            } else {
                delete basket[str_id];
                combination_slot.remove();
            }
            update_balance();
        });

    money_panel.appendChild(combination_slot);
}


function create_secondary_slot(slot, item, is_discount) {
    const secondary_slot = document.createElement('div');
    secondary_slot.className = 'secondary-slot';
    secondary_slot.innerHTML = `<h3 class="money-descr">${is_discount ? "Remise" : "Plein prix"}:
        ${item['nbr_items']}</h3>
        <p class="money-amount">${(item['price'] / 100).toFixed(2)}</p>`;
    slot.appendChild(secondary_slot);
}

function edit_combination_slot(slot, combination_id) {
    let int_comb_id, str_comb_id;
    if (typeof (combination_id) === 'string' && combination_id.startsWith('comb-')) {
        int_comb_id = parseInt(combination_id.substring(5));
        str_comb_id = combination_id;
    } else {
        int_comb_id = combination_id;
        str_comb_id = `comb-${combination_id}`;
    }
    const combination = combinations[int_comb_id];
    const price = (combination['price'] * basket[str_comb_id] / 100).toFixed(2);
    slot.querySelector('.money-amount').innerHTML = price + " €";
    slot.querySelector('.count-value').innerHTML = basket[str_comb_id];
}

function edit_money_slot(slot, product_id) {
    const product_name = products[product_id]['name'];
    const main_slot = slot.querySelector('.main-slot');
    let price = 0
    let nb_full_price = basket[product_id];  // number of items that are not subject to any discount

    // remove previous secondary slots
    for (let s of slot.querySelectorAll('.secondary-slot')) s.remove();

    // display secondary slots and calculate price considering discounts
    const discounts = get_price_decomposition(product_id, basket[product_id]);
    const full_price = discounts.pop();
    if (full_price['nbr_items'] > 0 && discounts.length > 0) {
        create_secondary_slot(slot, full_price, false);
    }
    if (discounts.length > 0) {
        for (const discount of discounts) {
            price += discount['price'];
            nb_full_price -= discount['nbr_items'];
            create_secondary_slot(slot, discount, true);
        }
    }
    main_slot.querySelector('.money-descr').innerHTML = product_name;
    price = ((price + nb_full_price * products[product_id]['price']) / 100).toFixed(2);
    main_slot.querySelector('.money-amount').innerHTML = price + " €";
    let count = slot.querySelector('.count-value');
    if (count !== null) count.innerHTML = basket[product_id];
}

/**
 * Retourne une décomposition des items en fonction des prix qui s'appliquent avec les remises
 * Chaque élément de la liste retournée est un objet contenant le prix et le nombre d'items
 * d'un groupe d'items.
 *
 * Le dernier élément de la liste contient toujours les items payés sans remise, même s'il y en a 0.
 * @param product_id
 * @param nb_items
 */
function get_price_decomposition(product_id, nb_items) {
    let price_decomposition = [];
    for (let i = products[product_id]['discount'].length - 1; i >= 0; i--) {
        const discount = products[product_id]['discount'][i];
        while (nb_items >= discount['nbr_items']) {
            nb_items -= discount['nbr_items'];
            price_decomposition.push({
                'price': discount['price'],
                'nbr_items': discount['nbr_items']
            });
        }
        if (nb_items === 0) break;
    }
    // items restants, payés plein tarif
    price_decomposition.push({
        'price': nb_items * products[product_id]['price'],
        'nbr_items': nb_items
    });
    return price_decomposition;
}

function get_price(product_id, nb_items) {
    if (typeof (product_id) === 'string' && product_id.startsWith('comb-')) {
        product_id = parseInt(product_id.substring(5));
        return combinations[product_id]['price'] * nb_items;
    }
    let price = 0;
    for (let i = products[product_id]['discount'].length - 1; i >= 0; i--) {
        const discount = products[product_id]['discount'][i];
        while (nb_items >= discount['nbr_items']) {
            price += discount['price'];
            nb_items -= discount['nbr_items'];
        }
        if (nb_items === 0) break;
    }
    return price + nb_items * products[product_id]['price'];
}

function update_balance() {
    let balance = starting_money;
    balance += parseInt(document.getElementById('add-money').value) * 100;
    for (let [id, nb_items] of Object.entries(basket)) {
        balance -= get_price(id, nb_items);
    }
    document.getElementById('final-balance').innerHTML = (balance / 100).toFixed(2) + " €";
}

function add_combination(combination_id, creator_product_id) {
    // Les combinaisons ont un id commençant par comb-
    // pour ne pas avoir de conflit avec les produits normaux
    let basket_comb_id = `comb-${combination_id}`;
    const combination = combinations[combination_id];
    const comb_slot = document.getElementById(basket_comb_id);
    if (comb_slot !== null) {
        basket[basket_comb_id] += 1;
        edit_combination_slot(comb_slot, combination_id)
    } else {
        basket[basket_comb_id] = 1;
        create_combination_slot(combination_id);
    }
    for (const product of combination['products']) {
        if (product !== creator_product_id) {
            remove_item(product)
        }
    }
    update_balance();
}

function add_item(product_id) {
    product_id = parseInt(product_id);
    if (combinations_for_product[product_id].length > 0) {
        for (const combination of combinations_for_product[product_id]) {
            let can_be_combined = true;
            for (const product of combinations[combination]['products']) {
                if (product !== product_id && (basket[product] === undefined || basket[product] === 0)) {
                    can_be_combined = false;
                    break;
                }
            }
            if (can_be_combined) {
                add_combination(combination, product_id);
                return;
            }
        }
    }
    const money_slot = document.getElementById(product_id);
    if (money_slot !== null) {
        basket[product_id] += 1;
        edit_money_slot(money_slot, product_id);
    } else {
        basket[product_id] = 1;
        create_money_slot(product_id);
    }
    update_balance();
}

function show_category(category_id) {
    let id = "group-" + category_id;
    let categories = document.getElementById('items').getElementsByClassName('product-group');
    for (const category of categories) {
        category.style.display = category.id === id ? 'block' : 'none';
    }
    const buttons = document.getElementById('items')
        .querySelector('.category-navigation')
        .querySelectorAll('button');
    for (const button of buttons) {
        button.classList.remove('active');
        if (button.value === category_id) {
            button.classList.add('active');
        }
    }
}

function remove_item(product_id) {
    const money_slot = document.getElementById(product_id);
    if (money_slot !== null) {
        if (basket[product_id] > 1) {
            basket[product_id] -= 1;
            edit_money_slot(money_slot, product_id);
        } else {
            money_slot.remove();
            delete basket[product_id];
        }
    }
    update_balance();
}

function confirm_money_add() {
    const money_input = document.getElementById('add-money');
    const money_value = parseInt(money_input.value);
    if (money_value >= 0 && money_value <= Math.round(100 - starting_money / 100)) {
        update_balance();
        money_input.blur();
    } else {
        money_input.value = 0;
        money_input.focus();
    }
}

const create_basket_event = () => {
    create_basket(parseInt(document.getElementById('add-money').value), basket);
};

function hide_confirmation_overlay() {
    console.log('hide');
    document.getElementById('confirmation-validate').removeEventListener('click', create_basket_event);
    document.getElementById('confirmation-overlay-content').classList.add('bottom');
    setTimeout(() => {
        document.getElementById('confirmation-overlay').classList.add('hide');
    }, 500)
}


function show_success_message_overlay() {
    hide_confirmation_overlay();
    let overlay = document.getElementById('server-response-overlay');
    overlay.classList.remove('hide');
    overlay.classList.add('success');
    overlay.querySelector('p').innerText = 'Commande validée';
    setTimeout(() => {
        overlay.classList.add('hide');
    }, 2500);
    setTimeout(() => {
        overlay.classList.remove('success');
    }, 3000);
}

function show_failure_message_overlay(message="Une erreur est survenue") {
    hide_confirmation_overlay();
    let overlay = document.getElementById('server-response-overlay');
    overlay.classList.remove('hide');
    overlay.classList.add('failure');
    overlay.querySelector('p').innerText = message;
    setTimeout(() => {
        overlay.classList.add('hide');
    }, 2500);
    setTimeout(() => {
        overlay.classList.remove('failure');
    }, 3000);
}


function create_basket(money_added, basket) {
    document.getElementById('confirmation-validate').disabled = true;
    document.body.style.cursor = 'wait';

    // l'objet panier contenait des combinaisons uniquement par convenance pour la manipulation du front
    // comme le serveur ne prend pas en compte les combinaisons, on retransforme les combinaisons en produits normaux
    let req_basket = Object.assign({}, basket);
    for (let [id, nb_items] of Object.entries(req_basket)) {
        if (id.startsWith('comb-')) {
            const comb_id = parseInt(id.substring(5));
            for (const product of combinations[comb_id]['products']) {
                if (req_basket[product] === undefined) {
                    req_basket[product] = 0;
                }
                req_basket[product] += nb_items;
                delete req_basket[id];
            }
        }
    }

    const basket_create_request = new Request('/eboutique/basket/create/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            mode: 'same-origin',
            body: JSON.stringify({
                money_added: money_added,
                basket: req_basket
            })
        }
    )
    const basket_validate_request = new Request('/eboutique/basket/validate/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        mode: 'same-origin',
    })
    fetch(basket_create_request).then(response => {
        if (response.status === 400) {
            console.log('Erreur 400');
        } else if (response.status === 200) {
            return response.json().then(data => {
                let basket_value = 0;
                for (let [id, nb_items] of Object.entries(basket)) {
                    basket_value += get_price(id, nb_items);
                }
                if (data['price'] === basket_value) {
                    if (money_added > 0) {
                        // TODO appel à l'API pour payer en ligne
                    } else {
                        fetch(basket_validate_request).then(r => {
                            if (r.ok) {
                                show_success_message_overlay();
                                setTimeout(() => {
                                    window.location.replace("/eboutique/");
                                }, 3000);
                            }
                            else show_failure_message_overlay(r.statusText);
                        });
                    }
                }
                return data;
            });
        }
    }).then((res) => {
        document.getElementById('confirmation-validate').disabled = false;
        document.body.style.cursor = 'default';
    });
}

function display_confirmation_overlay() {
    document.getElementById('confirmation-overlay').classList.remove('hide');
    document.getElementById('confirmation-overlay-content').classList.remove('bottom');
    let list = document.createElement('ul');
    let money_spent = parseInt(document.getElementById('add-money').value) * 100;
    const money_added = parseInt(document.getElementById('add-money').value);

    if (money_added > 0) {
        let li = document.createElement('li');
        li.innerHTML = `Ajout d'argent sur le compte AE : ${money_added} €`;
        list.appendChild(li);
    }
    for (const [id, nb_items] of Object.entries(basket)) {
        const money_spent_item = get_price(id, nb_items);
        money_spent -= money_spent_item;
        const item = document.createElement('li');
        const name = (id.startsWith('comb-')) ? combinations[parseInt(id.substring(5))]['name'] : products[id]['name'];
        item.innerHTML = `${name} (${nb_items}) : ${(money_spent_item / 100).toFixed(2)} €`;
        list.appendChild(item);
    }
    document.getElementById('confirmation-overlay-content').querySelector('ul').replaceWith(list);
    document.getElementById('confirmation-total-amount').innerHTML = 'Variation du solde : ' + (money_spent / 100).toFixed(2) + '€';
    document.getElementById('confirmation-balance').innerHTML = 'Solde final : ' + ((money_spent + starting_money) / 100).toFixed(2) + '€';

    document.getElementById('confirmation-validate')
        .addEventListener('click', create_basket_event);

    document.getElementById('confirmation-cancel').addEventListener('click', hide_confirmation_overlay);
}

function init_buttons_listeners() {
    document.getElementById('add-money').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') confirm_money_add();
    });

    document.getElementById('validation-button').querySelector('button')
        .addEventListener('click', display_confirmation_overlay);

    const buttons = document.getElementById('items').getElementsByClassName('item');
    for (const button of buttons) {
        button.addEventListener('click', () => add_item(get_product_id(button)));
    }

    const group_buttons = document.getElementById('items')
        .querySelector('.category-navigation')
        .querySelectorAll('button');
    for (const button of group_buttons) {
        button.addEventListener('click', () => show_category(button.value))
    }
}

document.addEventListener('DOMContentLoaded', init_buttons_listeners);