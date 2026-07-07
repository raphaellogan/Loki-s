async function carregarPagina(pagina) {
    const resposta = await fetch(`pages/views/${pagina}.html`);
    const html = await resposta.text();

    document.getElementById("app").innerHTML = html;
}

// Página inicial
carregarPagina("cadastro");
carregarPagina("login");