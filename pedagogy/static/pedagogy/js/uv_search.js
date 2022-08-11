function search_uv() {
    let form = document.forms["search-uv-form"];
    const url_search = new URLSearchParams(new FormData(form)).toString();
    let request = new Request(form.action + "?" + url_search, {
        method: form.method,
    });
    fetch(request).then(res => console.log(res.statusText))

}

document.getElementById("uv-search-button").addEventListener('click', search_uv);
