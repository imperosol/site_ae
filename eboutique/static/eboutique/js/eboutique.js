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

function edit_money_slot(slot, product_id) {
    const price = ((products[product_id]['price'] / 100) * basket[product_id]).toFixed(2);
    const product_name = products[product_id]['name'];
    slot.querySelector('.money-descr').innerHTML = product_name;
    slot.querySelector('.money-amount').innerHTML = price + " €";
    let count = slot.querySelector('.count-value');
    if (count !== null) count.innerHTML = basket[product_id];
}

function update_balance() {
    let balance = starting_money;
    balance += parseInt(document.getElementById('add-money').value) * 100;
    for (const [id, nb_items] of Object.entries(basket)) {
        balance -= products[id]['price'] * nb_items;
    }
    document.getElementById('final-balance').innerHTML = (balance / 100).toFixed(2) + " €";
}

function add_item(product_id) {
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


function create_basket(money_added, basket) {
    document.getElementById('confirmation-validate').disable = true;
    const request = new Request('/eboutique/buy/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            mode: 'same-origin',
            body: JSON.stringify({
                money_added: money_added,
                basket: basket
            })
        }
    )
    fetch(request).then(response => response.json())
        .then(() => {
            document.getElementById('confirmation-validate').disable = false
        })

}

function display_confirmation() {
    document.getElementById('confirmation-overlay').classList.remove('hide');
    document.getElementById('confirmation-content').classList.remove('bottom');
    let list = document.createElement('ul');
    let money_spent = parseInt(document.getElementById('add-money').value) * 100;
    const money_added = parseInt(document.getElementById('add-money').value);

    if (money_added > 0) {
        let li = document.createElement('li');
        li.innerHTML = `Ajout d'argent sur le compte AE : ${money_added} €`;
        list.appendChild(li);
    }
    for (const [id, nb_items] of Object.entries(basket)) {
        money_spent -= products[id]['price'] * nb_items;
        const item = document.createElement('li');
        item.innerHTML = products[id]['name'] + ' (' + nb_items + ') : ' + (products[id]['price'] * nb_items / 100).toFixed(2) + '€';
        list.appendChild(item);
    }
    document.getElementById('confirmation-content').querySelector('ul').replaceWith(list);
    document.getElementById('confirmation-total-amount').innerHTML = 'Variation du solde : ' + (money_spent / 100).toFixed(2) + '€';
    document.getElementById('confirmation-balance').innerHTML = 'Solde final : ' + ((money_spent + starting_money) / 100).toFixed(2) + '€';

    document.getElementById('confirmation-cancel').addEventListener('click', () => {
        document.getElementById('confirmation-content').classList.add('bottom');
        setTimeout(() => {
            document.getElementById('confirmation-overlay').classList.add('hide');
        }, 500)
    });
    document.getElementById('confirmation-validate').addEventListener('click', () => send_buy_request(money_added * 100, basket));
}

function init_buttons_listeners() {
    const buttons = document.getElementById('items').getElementsByClassName('item');
    document.getElementById('add-money').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') confirm_money_add();
    });

    document.getElementById('validation-button').querySelector('button')
        .addEventListener('click', display_confirmation);

    for (const button of buttons) {
        button.addEventListener('click', () => add_item(get_product_id(button)));
    }
}

document.addEventListener('DOMContentLoaded', init_buttons_listeners);