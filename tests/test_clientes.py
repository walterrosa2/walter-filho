"""Valida os cards de "Empresas e projetos atendidos" em um navegador real."""
import pytest


@pytest.fixture
def clientes(navegador, base_url):
    """Abre a página sem rede externa: cada logo remoto falha e aciona seu onerror."""
    pagina = navegador.new_page(viewport={"width": 1280, "height": 900})
    pagina.route(
        "**/*",
        lambda rota: rota.continue_()
        if rota.request.url.startswith(base_url)
        else rota.abort(),
    )
    pagina.goto(base_url)
    pagina.evaluate(
        "document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')"
    )
    pagina.wait_for_function(
        "[...document.querySelectorAll('.client-logo')].every(i => i.complete)"
    )
    pagina.wait_for_timeout(300)  # dá tempo de os eventos de erro rodarem
    yield pagina
    pagina.close()


def test_logo_remoto_que_falha_some_do_card(clientes):
    visiveis_quebrados = clientes.evaluate(
        """[...document.querySelectorAll('.client-logo')]
            .filter(i => !i.naturalWidth && i.style.display !== 'none')
            .map(i => i.alt)"""
    )
    assert visiveis_quebrados == []


def test_nenhum_logo_depende_do_clearbit(clientes):
    fontes = clientes.eval_on_selector_all(
        ".client-logo", "els => els.map(e => e.getAttribute('src'))"
    )
    assert fontes
    assert not [f for f in fontes if "clearbit" in f]


@pytest.mark.parametrize(
    "alt, arquivo",
    [
        ("Logo SBK Capital", "logos/sbk-capital.png"),
        ("Logo FAEPU", "logos/faepu.png"),
    ],
)
def test_logos_locais_carregam(clientes, alt, arquivo):
    logo = clientes.locator(f'.client-logo[alt="{alt}"]')
    assert logo.get_attribute("src") == arquivo
    assert logo.evaluate("el => el.naturalWidth") > 0


@pytest.mark.parametrize("nome", ["Castronaves", "Vector FIDC"])
def test_nome_do_cliente_com_grafia_correta(clientes, nome):
    assert clientes.locator(".client-copy strong", has_text=nome).count() == 1
    assert clientes.locator(f'.client-logo[alt="Logo {nome}"]').count() == 1


@pytest.mark.parametrize("grafia_antiga", ["CasAtronaves", "Vector FDIC"])
def test_grafia_antiga_nao_aparece(clientes, grafia_antiga):
    assert grafia_antiga not in clientes.content()
