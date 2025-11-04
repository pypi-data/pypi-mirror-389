import asyncio
import warnings
from datetime import datetime
import json
import ast
import io
import pyautogui
from pywinauto.application import Application
from pywinauto import keyboard
from pywinauto import Desktop
from collections import defaultdict
from rich.console import Console
import getpass
import time
import re
import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

from worker_automate_hub.api.client import (
    get_config_by_name,
    send_file,
    get_notas_produtos,
)
from worker_automate_hub.models.dto.rpa_historico_request_dto import (
    RpaHistoricoStatusEnum,
    RpaRetornoProcessoDTO,
    RpaTagDTO,
    RpaTagEnum,
)
from worker_automate_hub.models.dto.rpa_processo_entrada_dto import (
    RpaProcessoEntradaDTO,
)
from worker_automate_hub.utils.logger import logger
from pywinauto.keyboard import send_keys

# from worker_automate_hub.utils.toast import show_toast
from worker_automate_hub.utils.util import (
    send_to_webhook,
    extract_nf_number,  # permanece importado, mesmo sem uso
    faturar_pre_venda,
    find_element_center,
    find_target_position,
    kill_all_emsys,
    login_emsys,
    set_variable,
    take_screenshot,
    take_target_position,
    type_text_into_field,
    wait_nf_ready,
    wait_window_close,
    worker_sleep,
)

console = Console()

ASSETS_BASE_PATH = r"assets\devolucao_produtos"
# ASSETS_BASE_PATH = r"C:\Users\automatehub\Desktop\img_leo"
ALMOXARIFADO_DEFAULT = "50"


def _parse_int_tolerante(val):
    if val is None:
        return 0
    if isinstance(val, int):
        return val
    s = str(val).replace("\u00a0", "").strip()  # remove NBSP
    s = s.replace(".", "").replace(",", "")  # remove separadores comuns
    return int(float(s or 0))


def _coletar_itens_achatados(d: dict):
    descrs, qtds = {}, {}
    for k, v in d.items():
        m = re.match(r"^descricaoProduto(\d+)$", k, flags=re.I)
        if m:
            descrs[m.group(1)] = v
            continue
        m = re.match(r"^qtd(\d+)$", k, flags=re.I)
        if m:
            qtds[m.group(1)] = v
            continue

    itens = []
    idxs = sorted(set(descrs.keys()) | set(qtds.keys()), key=lambda x: int(x))
    for n in idxs:
        desc = (descrs.get(n) or "").strip()
        if not desc:
            continue
        qtd = _parse_int_tolerante(qtds.get(n, 0))
        if qtd <= 0:
            continue
        itens.append({"descricaoProduto": desc, "qtd": qtd})
    return itens


def normalize_config_entrada(cfg: dict) -> dict:
    """
    Se vier com 'itens': mantém e normaliza qtd -> int.
    Se vier como descricaoProdutoN/qtdN: converte para 'itens'.
    Preserva demais campos.
    """
    cfg = dict(cfg or {})
    if isinstance(cfg.get("itens"), list):
        itens_norm = []
        for it in cfg["itens"]:
            if not isinstance(it, dict):
                continue
            desc = str(it.get("descricaoProduto", "")).strip()
            if not desc:
                continue
            qtd = _parse_int_tolerante(it.get("qtd", it.get("quantidade", 0)))
            if qtd <= 0:
                continue
            itens_norm.append({"descricaoProduto": desc, "qtd": qtd})
        cfg["itens"] = itens_norm
        return cfg

    # formato achatado
    itens = _coletar_itens_achatados(cfg)
    cfg["itens"] = itens
    # remove chaves achatadas da saída (opcional)
    chaves_remover = [
        k for k in cfg.keys() if re.match(r"^(descricaoProduto|qtd)\d+$", k, flags=re.I)
    ]
    for k in chaves_remover:
        cfg.pop(k, None)
    return cfg
    

# --- fim do normalizador ---


async def devolucao_produtos(task: RpaProcessoEntradaDTO) -> RpaRetornoProcessoDTO:
    try:
        # Get config from BOF
        config = await get_config_by_name("login_emsys")
        console.print(task)

        # Seta config entrada na var nota para melhor entendimento (normalizando formatos)
        nota = normalize_config_entrada(task.configEntrada)
        itens = nota.get("itens", [])

        descricao_filial = task.configEntrada.get("descricaoFilial", "")
        empresa = descricao_filial.split(" - ")[0]
        estado = nota.get("estado", "")
        descricao_fornecedor = nota.get("descricaoFornecedor", "")
        historico_id = task.historico_id
        cod_fornecedor = descricao_fornecedor.split(" - ")[0]
        fornecedor = descricao_fornecedor.split(" - ")[1]
        identificador = nota.get("identificador", "")
        url_retorno = nota.get("urlRetorno", "")
        multiplicador_timeout = int(float(task.sistemas[0].timeout))
        set_variable("timeout_multiplicador", multiplicador_timeout)

        # ========= CHAMADA AO ENDPOINT E MONTAGEM DO DATA =========
        # res deve retornar {"lista": [...], "por_codigo": {cod: {...}}}
        res = await get_notas_produtos(int(cod_fornecedor), int(empresa), itens)
        by_code = res.get("por_codigo", {}) or {}  # dict dinâmico por código

        # ========= EXTRAÇÃO DE UM CFOP (PRIMEIRO ENCONTRADO) =========
        cfop = None  # Apenas um CFOP em variável
        for info in by_code.values():
            notas_raw = info.get("notas") or []
            # garante que seja lista
            if isinstance(notas_raw, (str, int)):
                notas_raw = [notas_raw]

            achou = False
            for n in notas_raw:
                try:
                    # Caso venha como string de dict: "{'nota': '1401414', 'cfop': '1102'}"
                    if isinstance(n, str) and n.strip().startswith("{"):
                        nota_dict = ast.literal_eval(n)
                    elif isinstance(n, dict):
                        nota_dict = n
                    else:
                        nota_dict = None

                    if isinstance(nota_dict, dict) and "cfop" in nota_dict:
                        cfop = nota_dict["cfop"]
                        achou = True
                        break
                except Exception:
                    continue
            if achou:
                break

        # Constrói os itens na estrutura usada no fluxo de UI
        itens_ui = []
        notas_encontradas = []  # acumula apenas os números das notas (strings) para deduplicar depois

        for it in itens:
            # aceita "descricaoProduto" contendo o código, ou "codigo"/"codigoProduto"
            desc = it.get("descricaoProduto", "") or ""
            nums = re.findall(r"\d+", desc)
            if not nums:
                # fallback: tenta campo "codigo" direto (se existir)
                cod_raw = it.get("codigo") or it.get("codigoProduto")
                if cod_raw is None:
                    continue
                try:
                    cod = int(re.findall(r"\d+", str(cod_raw))[0])
                except Exception:
                    continue
            else:
                cod = int(nums[0])

            # quantidade (como int > 0)
            qtd_raw = it.get("quantidade", it.get("qtd"))
            try:
                qtd = int(qtd_raw)
                if qtd <= 0:
                    continue
            except (TypeError, ValueError):
                continue

            info = by_code.get(cod) or {}
            valor_unit = float(info.get("valorUnitario", 0) or 0)

            # Normaliza "notas" para lista SÓ com os números das notas (strings)
            notas_item_raw = info.get("notas") or []
            if isinstance(notas_item_raw, (str, int)):
                notas_item_raw = [notas_item_raw]

            notas_item_nums = []
            for n in notas_item_raw:
                # 1) se já vier dict
                if isinstance(n, dict):
                    nota_num = n.get("nota")
                    if nota_num is not None:
                        notas_item_nums.append(str(nota_num))
                        continue

                # 2) se vier string de dict "{'nota': '1401414', 'cfop': '1102'}"
                if isinstance(n, str) and n.strip().startswith("{"):
                    try:
                        d = ast.literal_eval(n)
                        if isinstance(d, dict) and d.get("nota") is not None:
                            notas_item_nums.append(str(d["nota"]))
                            continue
                    except Exception:
                        pass

                # 3) fallback: manter como string (pode ser já o número)
                notas_item_nums.append(str(n))

            # Acumula para a lista geral (será deduplicada depois)
            notas_encontradas.extend(notas_item_nums)

            itens_ui.append(
                {
                    "codigo": cod,
                    "quantidade": qtd,
                    "valor_unitario": valor_unit,
                    "valor_total_item": round(valor_unit * qtd, 2),
                    "notas": notas_item_nums,  # vínculo item ↔ números das notas
                }
            )

        # Deduplica notas preservando a ordem de aparição
        nf_ref = list(dict.fromkeys(notas_encontradas))

        # Índice opcional: itens por cada nota (facilita inclusão na UI)
        itens_por_nota = defaultdict(list)
        for item in itens_ui:
            for n in item["notas"]:
                itens_por_nota[n].append(item)

        data = {
            "nf_referencia": nf_ref,  # ex.: ['1418727', '1410744']
            "itens": itens_ui,        # cada item com suas notas (apenas números)
            "totais": {
                "valor_final": round(sum(i["valor_total_item"] for i in itens_ui), 2)
            },
            "itens_por_nota": itens_por_nota,  # para uso direto no fluxo de UI
            "cfop": cfop,  # <<< CFOP único extraído e disponível no payload
        }
        # ========= FIM DA MONTAGEM DO DATA =========

        # Fecha a instancia do emsys - caso esteja aberta
        await kill_all_emsys()

        app = Application(backend="win32").start("C:\\Rezende\\EMSys3\\EMSys3_10.exe")
        warnings.filterwarnings(
            "ignore",
            category=UserWarning,
            message="32-bit application should be automated using 32-bit Python",
        )
        console.print("\nEMSys iniciando...", style="bold green")
        return_login = await login_emsys(config.conConfiguracao, app, task)

        if return_login.sucesso == True:
            console.print("Pesquisando por: Cadastro Pré Venda")
            type_text_into_field(
                "Cadastro Pre-Venda", app["TFrmMenuPrincipal"]["Edit"], True, "50"
            )
            pyautogui.press("enter")
            await worker_sleep(1)
            pyautogui.press("enter")
            console.print(
                f"\nPesquisa: 'Cadastro Pre Venda' realizada com sucesso",
                style="bold green",
            )
            await worker_sleep(3)
            try:
                app = Application().connect(class_name="TFrmSelecionaTipoPreVenda")
                select_prevenda_type = app["Selecione o Tipo de Pré-Venda"]

                if select_prevenda_type.exists():
                    tipo = select_prevenda_type.child_window(
                        class_name="TComboBox", found_index=0
                    )
                    tipo.select("Orçamento")
                    confirm = select_prevenda_type.child_window(
                        class_name="TDBIBitBtn", found_index=1
                    )
                    confirm.click()
            except:
                console.print(
                    "Sem tela de selecionar modelo de pre venda", style="bold green"
                )
        else:
            logger.info(f"\nError Message: {return_login.retorno}")
            console.print(f"\nError Message: {return_login.retorno}", style="bold red")
            return return_login

        await worker_sleep(7)

        # Condição da Pré-Venda
        console.print("Selecionando a Condição da Pré-Venda\n")
        app = Application().connect(class_name="TFrmPreVenda")
        main_window = app["TFrmPreVenda"]

        condicao_field = main_window.child_window(
            class_name="TDBIComboBox", found_index=2
        )
        condicao_field.select("21 DIAS")

        # Código do fornecedor
        input_cod_fornecedor = main_window.child_window(
            class_name="TDBIEditNumber", found_index=2
        )
        input_cod_fornecedor.click_input()
        await worker_sleep(0.2)
        keyboard.send_keys("{END}+{HOME}{DEL}")
        await worker_sleep(0.2)
        input_cod_fornecedor.type_keys(
            str(cod_fornecedor), with_spaces=True, set_foreground=True
        )
        keyboard.send_keys("{TAB}")
        await worker_sleep(5)

        # Popups
        try:
            app = Application().connect(class_name="TFrmSelecionaEndereco")
            app["TFrmSelecionaEndereco"].close()
            await worker_sleep(3)
            app = Application().connect(class_name="TMessageForm")
            app["TMessageForm"].child_window(
                class_name="TButton", found_index=0
            ).click()
        except:
            pass

        app = Application().connect(class_name="TFrmPreVenda")
        main_window = app["TFrmPreVenda"]
        console.print("Verificar estado...")
        cfop_dentro = ["5101", "5102", "5103", "5104", "1102"]
        if cfop not in cfop_dentro:
            modelo = "DEVOLUCAO DE COMPRA DE MERCADORIAS SC"
        else:
            modelo = "DEVOLUCAO DE COMPRA DE MERCADORIAS - TRIBUTADO"


        # Inserir modelo
        console.print("Inserir modelo...")
        select_modelo = main_window.child_window(
            class_name="TDBIComboBox", found_index=0
        )
        select_modelo.select(modelo)
        await worker_sleep(1)

        # Abrir guia de itens (por imagem)
        imagem_item = fr"{ASSETS_BASE_PATH}\itens.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_item, confidence=0.9)
            if pos:
                pyautogui.click(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")
        await worker_sleep(2)

        # Incluir item
        botao_incluir = main_window.child_window(
            title="Incluir", class_name="TDBIBitBtn"
        ).wrapper_object()
        botao_incluir.click_input()
        await worker_sleep(5)

        # =============== PREPARO DE DADOS ===============
        almoxarifado = f"{descricao_filial}50"

        # =============== ALMOXARIFADO ===============
        console.print("Inserir Almoxarifado...")
        # Abre tela de inclusão de item
        app_item = Application().connect(class_name="TFrmIncluiItemPreVenda")
        wnd_item = app_item["TFrmIncluiItemPreVenda"]
        input_almoxarifado = wnd_item.child_window(
            class_name="TDBIEditNumber", found_index=16
        )
        input_almoxarifado.click_input()
        await worker_sleep(1)
        keyboard.send_keys("{END}+{HOME}{DEL}")
        await worker_sleep(1)
        input_almoxarifado.type_keys(
            almoxarifado, with_spaces=True, set_foreground=True
        )
        keyboard.send_keys("{TAB}")
        await worker_sleep(1)

        # Dicionário para guardar os itens sem saldo / com saldo
        itens_sem_saldo = {}
        itens_com_saldo = {}

        # >>> NOVO: set para acumular SOMENTE notas dos itens com saldo
        notas_validas_set = set()
        # (opcional) controle de notas ligadas a itens sem saldo, útil para log
        notas_descartadas_set = set()

        # =============== LOOP POR ITEM (USANDO DADOS DA API) ===============
        for item in data["itens"]:
            await worker_sleep(2)
            # Abre tela de inclusão de item
            app_item = Application().connect(class_name="TFrmIncluiItemPreVenda")
            wnd_item = app_item["TFrmIncluiItemPreVenda"]
            codigo = str(item["codigo"])
            quantidade = str(item["quantidade"])
            val_unitario = f"{float(item['valor_unitario']):.2f}".replace(".", ",")
            item_notas = item.get("notas", [])

            # --- Código ---
            console.print("Inserir código...")
            input_codigo = wnd_item.child_window(
                class_name="TDBIEditNumber", found_index=15
            )
            input_codigo.click_input()
            await worker_sleep(1)
            keyboard.send_keys("{END}+{HOME}{DEL}")
            await worker_sleep(1)
            input_codigo.type_keys(codigo, with_spaces=True, set_foreground=True)
            keyboard.send_keys("{TAB}")
            await worker_sleep(5)
            try:
                # Verificar item sem saldo 
                app_item_ss = Application().connect(class_name="TFrmPesquisaItem")
                item_ss = app_item_ss["TFrmPesquisaItem"]
                btn_ss = item_ss.child_window(
                title="&Cancela", class_name="TDBIBitBtn").click_input()
                # adiciona no dicionário de erros
                itens_sem_saldo[codigo] = {
                    "quantidade": quantidade,
                    "valor_unitario": val_unitario,
                }
                continue

            except:
                pass

            # --- Unidade (UNI) ---
            console.print("Selecionar Unidade...")
            select_uni = wnd_item.child_window(class_name="TDBIComboBox", found_index=1)
            try:
                select_uni.select("UNI")
            except Exception:
                select_uni.set_focus()
                select_uni.expand()
                await worker_sleep(1)
                select_uni.type_keys("UNI", with_spaces=True, set_foreground=True)
                keyboard.send_keys("{ENTER}")
            keyboard.send_keys("{TAB}")
            await worker_sleep(1)

            # --- Quantidade ---
            console.print("Inserir quantidade...")
            wnd_item.child_window(
                class_name="TDBIEditNumber", found_index=8
            ).click_input()
            await worker_sleep(1)
            keyboard.send_keys("{END}+{HOME}{DEL}")
            await worker_sleep(1)
            keyboard.send_keys(quantidade)
            keyboard.send_keys("{TAB}")
            await worker_sleep(1)

            # --- Valor Unitário via popup ---
            console.print("Inserir valor unitário...")
            wnd_item.child_window(
                class_name="TDBIEditNumber", found_index=6
            ).click_input()
            await worker_sleep(1)
            keyboard.send_keys("{TAB}")
            await worker_sleep(1)
            keyboard.send_keys("{ENTER}")
            await worker_sleep(1)

            app_preco = Application().connect(class_name="TFrmInputBoxNumero")
            wnd_preco = app_preco["TFrmInputBoxNumero"]

            campo_preco = wnd_preco.child_window(
                class_name="TDBIEditNumber", found_index=0
            )
            campo_preco.click_input()
            await worker_sleep(1)
            keyboard.send_keys("{END}+{HOME}{DEL}")
            await worker_sleep(1)
            campo_preco.type_keys(val_unitario, with_spaces=True, set_foreground=True)
            await worker_sleep(1)
            wnd_preco.child_window(class_name="TBitBtn", found_index=1).click_input()
            await worker_sleep(2)

            # --- Confirmar Incluir ---
            console.print("Confirmar inclusão do item...")
            app_prevenda = Application().connect(class_name="TFrmIncluiItemPreVenda")
            wnd_prevenda = app_prevenda["TFrmIncluiItemPreVenda"]
            botao_incluir = wnd_prevenda.child_window(
                title="&Incluir", class_name="TDBIBitBtn"
            ).wrapper_object()
            botao_incluir.click_input()

            await worker_sleep(4)

            # ================== VERIFICAÇÃO DE SALDO ==================
            # >>> REESCRITO para deixar claro had_saldo e alimentar notas_validas_set
            had_saldo = True
            try:
                console.print("Verificar mensagem de saldo menor....")
                img_saldo =fr"{ASSETS_BASE_PATH}\saldo_menor.png"
                img_saldo_bool = False

                for _ in range(10):
                    pos = pyautogui.locateCenterOnScreen(img_saldo, confidence=0.9)
                    if pos:
                        console.print(
                            f"Saldo disponível menor para o item {codigo}: {quantidade} x {val_unitario}"
                        )

                        # adiciona no dicionário de erros
                        itens_sem_saldo[codigo] = {
                            "quantidade": quantidade,
                            "valor_unitario": val_unitario,
                        }

                        # fecha a mensagem
                        app = Application().connect(class_name="TMessageForm")
                        main_window_msg = app["TMessageForm"]
                        btn_no = main_window_msg.child_window(
                            title="&No", class_name="TButton"
                        )
                        btn_no.click_input()

                        # clica em limpar
                        app = Application().connect(class_name="TFrmIncluiItemPreVenda")
                        main_window_limpa = app["TFrmIncluiItemPreVenda"]
                        btn_limpa = main_window_limpa.child_window(
                            title="&Limpa", class_name="TDBIBitBtn"
                        )
                        btn_limpa.click_input()

                        img_saldo_bool = True
                        had_saldo = False
                        break
                    await worker_sleep(1)

                await worker_sleep(3)

                if img_saldo_bool:
                    # saldo menor que quantidade
                    # (já inserido em itens_sem_saldo; também marcaremos as notas deste item como descartadas)
                    for n in item_notas:
                        notas_descartadas_set.add(str(n))
                    continue

            except Exception:
                # Se der algum erro na verificação da imagem, assumimos sucesso (com saldo)
                had_saldo = True

            # Se teve saldo, registra e marca notas válidas
            if had_saldo:
                console.print(f"Item {codigo} incluído com sucesso.")
                itens_com_saldo[codigo] = {
                    "quantidade": quantidade,
                    "valor_unitario": val_unitario,
                }
                for n in item_notas:
                    notas_validas_set.add(str(n))
                continue

        # Depois de processar todos os itens:
        if itens_sem_saldo and not itens_com_saldo:
            # Todos os itens ficaram sem saldo → para aqui
            log_msg = "Todos os itens estão com saldo menor que a quantidade:\n" + "\n".join(
                f"- Código: {cod} | Quantidade: {dados['quantidade']} | Valor Unitário: {dados['valor_unitario']}"
                for cod, dados in itens_sem_saldo.items()
            )
            return RpaRetornoProcessoDTO(
                sucesso=False,
                retorno=log_msg.strip(),
                status=RpaHistoricoStatusEnum.Falha,
                tags=[RpaTagDTO(descricao=RpaTagEnum.Negocio)],
            )

        # Caso contrário, existe pelo menos 1 com saldo → segue o fluxo
        console.print("Há itens com saldo. Continuando o fluxo até o final...")

        try:
            # Liberação de preço (se aparecer)
            app = Application().connect(class_name="TFrmUsuariosLiberacaoPreco")
            login = app.window(class_name="TFrmUsuariosLiberacaoPreco")
            login.child_window(class_name="TEdit", found_index=0).click_input()
            login.type_keys("rpa.marvin", with_spaces=True, set_foreground=True)
            login.child_window(class_name="TEdit", found_index=1).click_input()
            login.type_keys("cba321", with_spaces=True, set_foreground=True)
            login.child_window(class_name="TBitBtn", found_index=0).click_input()
        except:
            pass

        # Clicar em fechar
        wnd_prevenda.close()

        await worker_sleep(3)

        # Clicar em recebimentos
        console.print("Clicar em recebimentos...")
        imagem_item = fr"{ASSETS_BASE_PATH}\btn_recebimentos.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_item, confidence=0.9)
            if pos:
                pyautogui.doubleClick(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")

        await worker_sleep(3)

        # Clicar em Parcelamento
        console.print("Clicar em parcelamento...")
        imagem_parc = fr"{ASSETS_BASE_PATH}\btn_parcelamento.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_parc, confidence=0.8)
            if pos:
                pyautogui.doubleClick(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")

        await worker_sleep(3)

        # Volta pra janela de pre venda
        app = Application().connect(class_name="TFrmPreVenda")
        main_window = app["TFrmPreVenda"]

        # Condição de recebimento (boleto)
        console.print("Selecionar boleto...")
        condicao_field = main_window.child_window(
            class_name="TDBIComboBox", found_index=0
        )
        try:
            condicao_field.select("BANCO DO BRASIL BOLETO")
            print("Selecionado: BANCO DO BRASIL BOLETO")
        except Exception as e:
            print(
                f"Não foi possível selecionar 'BANCO DO BRASIL BOLETO' ({e}). Tentando 'BOLETO'..."
            )
            try:
                condicao_field.select("BOLETO")
                print("Selecionado: BOLETO")
            except Exception as e2:
                print(f"❌ Falha também ao selecionar 'BOLETO': {e2}")

        # Clicar em Incluir
        console.print("Incluir registro...")
        imagem_incluir = fr"{ASSETS_BASE_PATH}\IncluirRegistro.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_incluir, confidence=0.8)
            if pos:
                pyautogui.click(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")

        await worker_sleep(3)

        # Capturar número da pré-venda
        console.print("Capturar número da pré-venda...")
        numero_pre_venda = None
        timeout = 10
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                win = Desktop(backend="win32").window(title_re=".*Informa.*")
                if not win.exists(timeout=0.2):
                    time.sleep(0.3)
                    continue
                win.set_focus()

                textos = []
                try:
                    textos.append(win.window_text())
                except:
                    pass
                try:
                    textos += [t for t in win.wrapper_object().texts() if t]
                except:
                    pass
                try:
                    for st in win.children(class_name="Static"):
                        textos += [t for t in st.texts() if t]
                except:
                    pass

                texto = "\n".join([t for t in textos if t])
                if ("Venda inclu" in texto) or ("Pré" in texto) or ("Pr" in texto):
                    m = re.search(r"\b(\d{3,}-\d{1,})\b", texto)
                    if m:
                        numero_pre_venda = m.group(1)

                    clicked = False
                    for title in ("OK", "&OK"):
                        try:
                            win.child_window(
                                title=title, class_name="TButton"
                            ).click_input()
                            clicked = True
                            break
                        except:
                            pass
                    if not clicked:
                        try:
                            win.type_keys("{ENTER}")
                        except:
                            pass
                    break
            except:
                time.sleep(0.3)

        print("Número da pré-venda:", numero_pre_venda)
        await worker_sleep(5)

        # Confirmar pré-venda (Yes)
        console.print("Confirmar pré-venda...")
        app = Application().connect(class_name="TMessageForm")
        main_window = app["TMessageForm"]
        btn_ok = main_window.child_window(title="&Yes", class_name="TButton")
        btn_ok.click_input()
        await worker_sleep(4)

        # Botão confirma
        app = Application().connect(class_name="TFrmPreVenda")
        main_window = app["TFrmPreVenda"]
        btn_confirmar = main_window.child_window(
            title="&Confirma", class_name="TBitBtn"
        )
        btn_confirmar.click_input()
        await worker_sleep(4)

        # Confirmar (Yes)
        app = Application().connect(class_name="TMessageForm")
        main_window = app["TMessageForm"]
        btn_confirmar = main_window.child_window(title="&Yes", class_name="TButton")
        btn_confirmar.click_input()
        await worker_sleep(5)

        # Fechar "Informação"
        for _ in range(10):
            try:
                dlg = Desktop(backend="win32").window(
                    title_re="Informação", class_name="#32770"
                )
                if dlg.exists(timeout=1):
                    dlg.child_window(title="OK").click_input()
                    print("✅ Fechou janela 'Informação'.")
                    break
            except:
                pass
            time.sleep(1)

        await worker_sleep(3)

        # Faturar
        console.print("Clicar em faturar...")
        app = Application().connect(class_name="TFrmPreVenda")
        main_window = app["TFrmPreVenda"]
        main_window.set_focus()
        btn_faturar = main_window.child_window(title="&Faturar", class_name="TBitBtn")
        btn_faturar.click_input()
        await worker_sleep(5)
        print("Botão 'Faturar' clicado com sucesso!")

        # Recalcular Parcelas? (Yes)
        console.print("Clicar em recalcular parcelas...")
        app = Application().connect(class_name="TMessageForm")
        main_window = app["TMessageForm"]
        main_window.set_focus()
        btn_confirmar = main_window.child_window(title="&Yes", class_name="TButton")
        btn_confirmar.click_input()

        for _ in range(10):
            try:
                dlg = Desktop(backend="win32").window(
                    title_re="Parcelas - Nota Fiscal Sa", class_name="#32770"
                )
                if dlg.exists(timeout=1):
                    dlg.child_window(title="&Não").click_input()
                    print("Clicou em Não")
                    break
            except:
                pass

        await worker_sleep(20)

        # Notas referenciadas
        console.print("CLicar em notas referenciadas...")
        imagem_notas_ref = fr"{ASSETS_BASE_PATH}\notas_referenciadas.png"
        for _ in range(20):
            pos = pyautogui.locateCenterOnScreen(imagem_notas_ref, confidence=0.8)
            if pos:
                pyautogui.click(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")

        await worker_sleep(2)

        # Faturamento Pré-venda
        app = Application().connect(class_name="TFrmDadosFaturamentoPreVenda")
        main_window = app["TFrmDadosFaturamentoPreVenda"]
        main_window.set_focus()

        # Radio Entrada
        main_window.child_window(
            title="Entrada", class_name="TDBIRadioButton"
        ).click_input()
        console.print("Clicado em 'Entrada'")
        await worker_sleep(4)

        # ====== FILTRAR NOTAS VÁLIDAS ======
        todas_as_notas = [str(n) for n in data.get("nf_referencia", [])]
        notas_validas_ordenadas = [n for n in todas_as_notas if n in notas_validas_set]
        notas_descartadas = [n for n in todas_as_notas if n not in notas_validas_set]

        console.print(
            f"[green]Notas a referenciar (itens com saldo): {notas_validas_ordenadas}[/]"
        )
        if notas_descartadas:
            console.print(
                f"[yellow]Notas descartadas (apenas itens sem saldo): {notas_descartadas}[/]"
            )

        # >>> NOVO: nota_arquivo (primeira válida; fallback: pré-venda ou timestamp) - SEM extract_nf_number
        if notas_validas_ordenadas:
            nota_arquivo = re.sub(r"\D+", "", str(notas_validas_ordenadas[0])) or str(
                notas_validas_ordenadas[0]
            )
        else:
            if numero_pre_venda:
                nota_arquivo = re.sub(r"\D+", "", str(numero_pre_venda)) or str(
                    numero_pre_venda
                )
            else:
                nota_arquivo = datetime.now().strftime("%Y%m%d%H%M%S")

        # === LOOP REFERENCIANDO APENAS NOTAS VÁLIDAS ===
        for nf_ref_atual in notas_validas_ordenadas:
            itens_da_nota = data.get("itens_por_nota", {}).get(nf_ref_atual, [])
            if not itens_da_nota:
                console.print(
                    f"[amarelo]Nenhum item associado à nota {nf_ref_atual}. Pulando...[/]"
                )
                continue

            console.print(f"[cyan]Processando nota {nf_ref_atual}...[/]")

            # 1) Focar e limpar o campo da nota
            input_num_nota = main_window.child_window(class_name="TDBIEditDescription")
            input_num_nota.set_focus()
            try:
                input_num_nota.select()  # alguns campos suportam select()
            except Exception:
                pass
            keyboard.send_keys("^a{DEL}")  # Ctrl+A + Delete (fallback)
            await worker_sleep(0.4)

            # 2) Digitar a nota e confirmar
            input_num_nota.type_keys(
                str(nf_ref_atual), with_spaces=True, set_foreground=True
            )
            await worker_sleep(0.6)
            keyboard.send_keys("{ENTER}")
            await worker_sleep(0.6)

            # Clicar em incluir itens (folha de papel com +)
            app = Application().connect(class_name="TFrmDadosFaturamentoPreVenda")
            main_window = app["TFrmDadosFaturamentoPreVenda"]

            # Clica no botão identificado como TDBIBitBtn2 (control_id 918912)
            main_window.child_window(
                class_name="TDBIBitBtn", found_index=1
            ).click_input()

            print("Botão clicado com sucesso!")
            console.print(f"Incluindo itens vinculados à nota {nf_ref_atual}...")

        # Aba mensagens
        console.print("Clicar em mensagens...")
        imagem_notas_ref = fr"{ASSETS_BASE_PATH}\aba_mensagem.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_notas_ref, confidence=0.9)
            if pos:
                pyautogui.click(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")
        await worker_sleep(5)

        # Mensagem interna
        imagem_notas_ref = fr"{ASSETS_BASE_PATH}\mensagem_interna.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_notas_ref, confidence=0.8)
            if pos:
                pyautogui.click(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")
        await worker_sleep(4)

        # Inserir mensagem padrão
        console.print("Inserir mensagem...")
        lista_fornecedores = ["Disbal", "Pepsico", "Punta Balena"]
        mensagem = (
            "PRODUTOS VENCIDOS"
            if fornecedor in lista_fornecedores
            else "ACORDO COMERCIAL"
        )
        input_mensagem = main_window.child_window(class_name="TDBIMemo", found_index=0)
        input_mensagem.type_keys(mensagem, with_spaces=True, set_foreground=True)

        # Aba itens
        imagem_itens = fr"{ASSETS_BASE_PATH}\aba_itens.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_itens, confidence=0.9)
            if pos:
                pyautogui.click(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")

        await worker_sleep(3)

        # Corrige tributação
        console.print("Corrigir tributação...")
        imagem_itens = fr"{ASSETS_BASE_PATH}\corrige_tributacao.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_itens, confidence=0.9)
            if pos:
                pyautogui.click(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do tributacao não encontrada na tela.")

        await worker_sleep(3)

        # Selecionar tributação
        console.print("Selecionar tributação...")
        app = Application().connect(class_name="TFrmDadosTributacaoProdutoPreVenda")
        trib = app["TFrmDadosTributacaoProdutoPreVenda"]

        if "disbal" in fornecedor.lower():
            select_trib = trib.child_window(class_name="TDBIComboBox", found_index=4)
            select_trib.select("020 - 020 - ICMS 12% RED. BASE 41,667")

        elif "punta balena" in fornecedor.lower():
            select_trib = trib.child_window(class_name="TDBIComboBox", found_index=4)
            select_trib.select("000 - 000 - ICMS - 12%")

        elif "vitrola" in fornecedor.lower():
            select_trib = trib.child_window(class_name="TDBIComboBox", found_index=4)
            select_trib.select("041 - 041 - ICMS - NAO INCIDENTE ")

        elif estado == "RS" and "pepsico" in fornecedor.lower():
            select_trib = trib.child_window(class_name="TDBIComboBox", found_index=4)
            select_trib.select("051 - 051 - ICMS 17% RED BC 29,4118% - TRIBUT.CORRETA")
            print("Selecionado: 051 - 051 - ICMS 17% RED BC 29,4118% - TRIBUT.CORRETA")
        
        elif estado == "RS":
            select_trib = trib.child_window(class_name="TDBIComboBox", found_index=4)
            select_trib.select("051 - 051 - ICMS 17% RED BC 29,4118% - TRIBUT.CORRETA")
            print("Selecionado: 051 - 051 - ICMS 17% RED BC 29,4118% - TRIBUT.CORRETA")
        
        elif estado == "SC":
            select_trib = trib.child_window(class_name="TDBIComboBox", found_index=4)
            select_trib.select("000 - 000 - ICMS - 12%")
            print("Selecionado: 000 - 000 - ICMS - 12%")
        
        else:
            print("Estado diferente dos mapeados")

        await worker_sleep(2)

        trib.child_window(title="&OK", class_name="TBitBtn").click_input()

        await worker_sleep(1)

        # Aba principal
        imagem_principal = fr"{ASSETS_BASE_PATH}\aba_principal.png"
        for _ in range(10):
            pos = pyautogui.locateCenterOnScreen(imagem_principal, confidence=0.9)
            if pos:
                pyautogui.click(pos)
                break
            await worker_sleep(1)
        else:
            print("Imagem do item não encontrada na tela.")

        await worker_sleep(5)

        # DANFE 077
        console.print(
            "Selecionar NFe - NOTA FISCAL ELETRONICA PROPRIA - DANFE SERIE 077..."
        )
        app = Application().connect(class_name="TFrmDadosFaturamentoPreVenda")
        main_window = app["TFrmDadosFaturamentoPreVenda"]
        select_danfe = main_window.child_window(
            class_name="TDBIComboBox", found_index=1
        )
        select_danfe.select("NFe - NOTA FISCAL ELETRONICA PROPRIA - DANFE SERIE 077")

        await worker_sleep(2)

        # OK
        main_window.child_window(title="&OK", class_name="TBitBtn").click_input()

        await worker_sleep(3)

        # Faturar pré-venda (Yes)
        app = Application().connect(class_name="TMessageForm")
        main_window = app["TMessageForm"]
        main_window.child_window(class_name="TButton", found_index=1).click()

        await worker_sleep(5)

        # Faturar pré-venda (Yes)
        app = Application().connect(class_name="TMessageForm")
        main_window = app["TMessageForm"]
        main_window.child_window(
            title="Transmitir e &Imprimir", class_name="TButton"
        ).click_input()

        await worker_sleep(10)

        # Diálogo impressão
        console.print("Confirmar impressão...")
        app = Application().connect(class_name="TppPrintDialog")
        main_window = app["TppPrintDialog"]
        main_window.child_window(title="OK", class_name="TButton").click()

        await worker_sleep(5)

        console.print(f"NAVEGANDO NA TELA DE SALVAR RELATORIO\n")
        # INSERINDO O DIRETORIO E SALVANDO O ARQUIVO
        try:
            app = Application().connect(title="Salvar Saída de Impressão como")
            main_window = app["Dialog"]
            console.print("Tela 'Salvar' encontrada!")

            console.print("Interagindo com a tela 'Salvar'...\n")
            username = getpass.getuser()

            # Preenche o nome do arquivo - SOMENTE número da nota
            path_to_txt = f"C:\\Users\\{username}\\Downloads\\devolucao_nf_{estado}_{nota_arquivo}"

            main_window.type_keys("%n")
            pyautogui.write(path_to_txt)
            await worker_sleep(1)
            main_window.type_keys("%l")
            console.print("Arquivo salvo com sucesso...\n")
            await worker_sleep(8)
        except Exception as e:
            retorno = f"Não foi salvar o arquivo: {e}"
            return RpaRetornoProcessoDTO(
                sucesso=False,
                retorno=retorno,
                status=RpaHistoricoStatusEnum.Falha,
                tags=[RpaTagDTO(descricao=RpaTagEnum.Tecnico)],
            )

        with open(f"{path_to_txt}.pdf", "rb") as file:
            file_bytes = io.BytesIO(file.read())

        desArquivo = f"devolucao_nf_{estado}_{nota_arquivo}.pdf"
        try:
            await send_file(
                historico_id, desArquivo, "pdf", file_bytes, file_extension="pdf"
            )
            os.remove(f"{path_to_txt}.pdf")
        except Exception as e:
            result = (
                f"Arquivo gerado com sucesso, porém erro ao enviar para o backoffice: {e} "
                f"- Arquivo salvo em {path_to_txt}.pdf"
            )
            console.print(result, style="bold red")
            return RpaRetornoProcessoDTO(
                sucesso=False,
                retorno=result,
                status=RpaHistoricoStatusEnum.Falha,
                tags=[RpaTagDTO(descricao=RpaTagEnum.Tecnico)],
            )

    except Exception as ex:
        log_msg = f"Error: {ex}"
        print(ex)
        return RpaRetornoProcessoDTO(
            sucesso=False,
            retorno=log_msg,
            status=RpaHistoricoStatusEnum.Falha,
            tags=[RpaTagDTO(descricao=RpaTagEnum.Negocio)],
        )

    # ============== RESUMO FINAL ==============
    def _fmt_linha(cod, dados):
        return f"- Código: {cod} | Quantidade: {dados.get('quantidade')} | Valor Unitário: {dados.get('valor_unitario')}"

    resumo_partes = []

    if itens_com_saldo:
        lista_ok = "\n".join(_fmt_linha(c, d) for c, d in list(itens_com_saldo.items()))
        resumo_partes.append(
            "✅ Itens incluídos:\n" + (lista_ok if lista_ok else "(vazio)")
        )

    if itens_sem_saldo:
        lista_sem = "\n".join(
            _fmt_linha(c, d) for c, d in list(itens_sem_saldo.items())
        )
        resumo_partes.append(
            "⚠️ Itens sem saldo:\n" + (lista_sem if lista_sem else "(vazio)")
        )

    # (Opcional) resumo sobre notas válidas/descartadas
    try:
        resumo_partes.append(
            "🧾 Notas referenciadas: " + ", ".join(sorted(list(notas_validas_set)))
            if notas_validas_set
            else "🧾 Notas referenciadas: (nenhuma)"
        )
    except:
        pass

    resumo_txt = (
        "\n\n".join(resumo_partes) if resumo_partes else "Nenhum item processado."
    )

    return RpaRetornoProcessoDTO(
        sucesso=True,
        retorno=f"Processo concluído.\n\n{resumo_txt}",
        status=RpaHistoricoStatusEnum.Sucesso,
        tags=[RpaTagDTO(descricao=RpaTagEnum.Negocio)],
    )
