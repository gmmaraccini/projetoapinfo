import re
import time
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import config  # Importa as configurações

def extrair_telefones_validos(texto):
    """
    Extrai celulares (9 dígitos) e fixos (8 dígitos).
    Formata tudo para o padrão internacional: 55 + DDD + Numero.
    """
    if not texto: return []
    
    # REGEX ATUALIZADA: Aceita números começando de 2 a 9 (Fixo e Celular)
    # Grupo 1: DDD (Opcional)
    # Grupo 2: Prefixo (2 a 9, com 4 ou 5 digitos)
    # Grupo 3: Sufixo (4 digitos)
    padrao = r'(?:\(?([1-9][0-9])\)?\s?)?([2-9]\d{3,4})[\s-]?(\d{4})'
    
    encontrados = re.findall(padrao, texto)
    lista_formatada = []
    
    for match in encontrados:
        ddd, parte1, parte2 = match[0], match[1], match[2]
        numero_limpo = f"{parte1}{parte2}"
        
        # Filtro de tamanho mínimo (evita pegar anos como 2023, 2024)
        if len(numero_limpo) < 8:
            continue

        if ddd:
            numero_final = f"55{ddd}{numero_limpo}"
        else:
            numero_final = f"55{config.DDD_PADRAO}{numero_limpo}"
            
        lista_formatada.append(numero_final)
        
    return list(set(lista_formatada))

def fechar_aba_segura(driver, janela_retorno):
    """Fecha a aba atual e volta para a janela de retorno."""
    try:
        if len(driver.window_handles) > 1:
            driver.close()
    except: pass
    
    try:
        driver.switch_to.window(janela_retorno)
    except:
        if len(driver.window_handles) > 0:
            driver.switch_to.window(driver.window_handles[-1])

def processar_envios_whatsapp(driver, telefones, texto_mensagem, janela_principal):
    """
    Recebe uma lista de telefones e envia a mensagem para cada um.
    """
    if not telefones:
        print("   ❌ Nenhum telefone válido encontrado.")
        return

    print(f"   📱 Telefones encontrados: {telefones}")
    msg_encoded = urllib.parse.quote(texto_mensagem)

    for fone in telefones:
        print(f"   💬 Abrindo WhatsApp para: {fone}...")
        link_wa = f"https://web.whatsapp.com/send?phone={fone}&text={msg_encoded}"
        
        # Abre nova aba
        driver.execute_script(f"window.open('{link_wa}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        
        try:
            # === LOGICA BLINDADA DE ENVIO ===
            print("      -> Aguardando (15s)...")
            time.sleep(15) # Tempo para carregar contato e chat

            # 1. Verifica se deu erro de número inválido
            try:
                aviso = driver.find_elements(By.XPATH, '//*[contains(text(), "inválido") or contains(text(), "invalid")]')
                if aviso and aviso[0].is_displayed():
                    print(f"      ❌ Número Inválido (WhatsApp não aceitou).")
                    fechar_aba_segura(driver, janela_principal)
                    continue 
            except: pass

            # 2. Tenta Enviar (Botão ou Enter)
            enviado = False
            print("      -> Tentando enviar...")
            
            try:
                # Tenta clicar no botão enviar
                btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='send']"))
                )
                btn.click()
                enviado = True
                print("      ✅ Enviado (Clique no Botão).")
            except:
                # Se falhar, tenta dar Enter na caixa
                try:
                    caixa = driver.find_element(By.CSS_SELECTOR, '#main footer div[contenteditable="true"]')
                    caixa.send_keys(Keys.ENTER)
                    enviado = True
                    print("      ✅ Enviado (Enter na Caixa).")
                except:
                    print("      ⚠️ Falha: Não achei botão nem caixa de texto.")

            if enviado:
                time.sleep(5) # Espera visual para garantir saída da mensagem

        except Exception as e:
            print(f"      ❌ Erro crítico no envio: {e}")
        
        # Fecha o zap e volta para a janela principal (Vaga ou Lista)
        fechar_aba_segura(driver, janela_principal)