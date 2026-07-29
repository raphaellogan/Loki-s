// função que insere HTML e executa os scripts que vieram dentro dele
function inserirHtmlComScripts(elemento, html) {

    // Insere o HTML
    elemento.innerHTML = html;

    // Procura todos os scripts inseridos
    const scripts = elemento.querySelectorAll("script");

    scripts.forEach(scriptAntigo => {

        // Cria um script novo
        const scriptNovo = document.createElement("script");

        // Copia os atributos do script antigo
        for (const atributo of scriptAntigo.attributes) {

            scriptNovo.setAttribute(
                atributo.name,
                atributo.value
            );

        }

        // Copia o código JavaScript
        scriptNovo.textContent = scriptAntigo.textContent;

        // Substitui o script antigo pelo novo
        // Isso faz o navegador executar o script
        scriptAntigo.replaceWith(scriptNovo);

    });

}


// função assíncrona para que só carregue quando receber os dados
async function carregarPagina(pagina) {

    const paginasSemLayout = [
        "login",
        "cadastro",
        "configuracoes",
        "grafico"
    ];

    // caso sejam páginas sem layout
    if (paginasSemLayout.includes(pagina)) {

        const resposta = await fetch(`pages/${pagina}.html`);
        const html = await resposta.text();

        inserirHtmlComScripts(
            document.getElementById("app"),
            html
        );

    } else {

        // alterar essa parte depois para validar no servidor
        // ao invés de validar no frontend
        const respostaLayout = await fetch(
            "layouts/barra-lateral-almoxarife.html"
        );

        const layout = await respostaLayout.text();

        document.getElementById("app").innerHTML = layout;

        // mudar "almoxarife" para outro perfil futuramente
        const respostaPagina = await fetch(
            `pages/almoxarife/${pagina}.html`
        );

        const paginaHtml = await respostaPagina.text();

        inserirHtmlComScripts(
            document.getElementById("conteudo"),
            paginaHtml
        );

    }

}


async function navegar(event, pagina) {

    // impede o link de abrir normalmente,
    // mantendo o comportamento da SPA
    event.preventDefault();

    history.pushState(null, "", `/${pagina}`);

    await carregarPagina(pagina);

    marcarMenu(pagina);

}


// função que deixa o menu da página atual destacado
function marcarMenu(pagina) {

    document.querySelectorAll(".menu a").forEach(link => {

        link.classList.toggle(
            "ativo",
            link.dataset.pagina === pagina
        );

    });

}


const pagina =
    window.location.pathname.substring(1);


window.addEventListener("popstate", async () => {

    const pagina =
        window.location.pathname.substring(1) || "cadastro";

    await carregarPagina(pagina);

    marcarMenu(pagina);

});


(async () => {

    await carregarPagina(pagina);

    marcarMenu(pagina);

})();