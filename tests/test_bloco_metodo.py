"""Valida o bloco "Método de consultoria" em um navegador real.

Como rodar, na raiz do projeto:
    py -3 -m pytest tests -q

Requer pytest e playwright (com o Chromium instalado).
"""
import pytest

LARGURA_ORIGINAL, ALTURA_ORIGINAL = 1752, 897


def abrir(navegador, base_url, largura, altura=900):
    pagina = navegador.new_page(viewport={"width": largura, "height": altura})
    # Logos de terceiros não fazem parte do que é testado aqui.
    pagina.route(
        "**/*",
        lambda rota: rota.continue_()
        if rota.request.url.startswith(base_url)
        else rota.abort(),
    )
    pagina.goto(base_url)
    imagem = pagina.locator("#metodo .method-frame img")
    imagem.scroll_into_view_if_needed()
    pagina.wait_for_function(
        "el => el.complete && el.naturalWidth > 0", arg=imagem.element_handle()
    )
    return pagina, imagem


def test_menu_aponta_para_o_bloco(navegador, base_url):
    pagina, _ = abrir(navegador, base_url, 1280)
    assert pagina.locator('.navlinks a[href="#metodo"]').inner_text() == "Método"
    assert pagina.locator("#metodo h2").inner_text() == "Método de consultoria"
    pagina.close()


def test_menu_fixo_nao_cobre_o_titulo_do_bloco(navegador, base_url):
    pagina, _ = abrir(navegador, base_url, 1280)
    pagina.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    pagina.locator('.navlinks a[href="#metodo"]').click()
    titulo = pagina.locator("#metodo .section-title").bounding_box()
    menu = pagina.locator(".topbar").bounding_box()
    assert titulo["y"] >= menu["y"] + menu["height"]
    pagina.close()


def test_bloco_fica_antes_da_plataforma_enthusia(navegador, base_url):
    pagina, _ = abrir(navegador, base_url, 1280)
    ids = pagina.eval_on_selector_all("main section[id]", "els => els.map(e => e.id)")
    assert ids.index("metodo") + 1 == ids.index("enthusia")
    pagina.close()


@pytest.mark.parametrize("largura", [1440, 1280, 830, 820, 390, 360])
def test_imagem_aparece_inteira_e_sem_rolagem_lateral(navegador, base_url, largura):
    pagina, imagem = abrir(navegador, base_url, largura)
    dados = imagem.evaluate(
        """el => {
            const r = el.getBoundingClientRect();
            const m = el.closest('.method-frame').getBoundingClientRect();
            return {
                naturalW: el.naturalWidth, naturalH: el.naturalHeight,
                w: r.width, h: r.height, fit: getComputedStyle(el).objectFit,
                dentro: r.left >= m.left && r.right <= m.right
                     && r.top >= m.top && r.bottom <= m.bottom,
                overflow: document.documentElement.scrollWidth > innerWidth,
            };
        }"""
    )
    assert (dados["naturalW"], dados["naturalH"]) == (LARGURA_ORIGINAL, ALTURA_ORIGINAL)
    assert dados["w"] / dados["h"] == pytest.approx(
        LARGURA_ORIGINAL / ALTURA_ORIGINAL, rel=0.005
    )
    assert dados["fit"] == "fill"
    assert dados["dentro"]
    assert not dados["overflow"]
    pagina.close()


def test_link_de_ampliar_abre_o_png_original(navegador, base_url):
    pagina, _ = abrir(navegador, base_url, 1280)
    href = pagina.locator("#metodo .method-frame").get_attribute("href")
    resposta = pagina.request.get(base_url + href)
    assert resposta.status == 200
    assert resposta.headers["content-type"] == "image/png"
    pagina.close()
