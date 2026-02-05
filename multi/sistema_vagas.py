import re
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === IMPORTAÇÕES DOS SEUS MÓDULOS ===
import config
import bot_whatsapp
from disparador import enviar_email_final

# ==============================================================================
# FUNÇÕES DE APOIO
# ==============================================================================

def get_text_safe(driver, by, value):
    try:
        element = driver.find_element(by, value)
        if element: return element.text
    except: pass
    return ""

def analisar_aderencia(descricao_vaga):
    if not descricao_vaga: return []
    desc_lower = descricao_vaga.lower()
    matches = []
    for skill in config.HARD_SKILLS:
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', desc_lower):
            matches.append(skill)
    for skill in config.SOFT_SKILLS:
        if skill.lower() in desc_lower:
            matches.append(skill)
    return sorted(list(set(matches)))

def verifica_pedido_salario(descricao_vaga):
    if not descricao_vaga: return ""
    desc_lower = descricao_vaga.lower()
    if any(termo in desc_lower for termo in config.TERMOS_SALARIO):
        return "\nPretensão salarial: R$ 8.000,00 ou a combinar dependendo dos benefícios."
    return ""

def varrer_site_profundo(driver, url_home):
    """
    Entra na Home, pega telefones, procura links de 'Contato' e pega mais telefones.
    Retorna uma lista única com tudo o que achou.
    """
    telefones_totais = set()
    
    print(f"   🌍 Iniciando varredura profunda: {url_home}...")
    
    # 1. Abre a Home
    driver.execute_script(f"window.open('{url_home}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    aba_empresa = driver.current_window_handle
    
    try:
        time.sleep(4)
        # Pega telefones da Home
        txt_home = get_text_safe(driver, By.TAG_NAME, "body")
        tels_home = bot_whatsapp.extrair_telefones_validos(txt_home)
        telefones_totais.update(tels_home)
        if tels_home: print(f"      -> Home: {len(tels_home)} números achados.")

        # 2. Procura links internos (Contato, Fale Conosco, etc)
        links_internos = []
        termos_busca = ['contato', 'fale', 'trabalhe', 'contact', 'work', 'atendimento']
        
        elementos_a = driver.find_elements(By.TAG_NAME, "a")
        for elem in elementos_a:
            try:
                href = elem.get_attribute("href")
                txt_link = elem.text.lower()
                
                if href and any(t in txt_link or t in href.lower() for t in termos_busca):
                    if "mailto:" not in href and "whatsapp" not in href:
                        links_internos.append(href)
            except: pass
        
        links_internos = list(set(links_internos))[:3]

        for link_pag in links_internos:
            try:
                print(f"      -> Visitando: {link_pag}...")
                driver.execute_script(f"window.open('{link_pag}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(3)
                
                txt_pag = get_text_safe(driver, By.TAG_NAME, "body")
                tels_pag = bot_whatsapp.extrair_telefones_validos(txt_pag)
                
                if tels_pag:
                    print(f"         + {len(tels_pag)} novos números.")
                    telefones_totais.update(tels_pag)
                
                bot_whatsapp.fechar_aba_segura(driver, aba_empresa)
            except:
                bot_whatsapp.fechar_aba_segura(driver, aba_empresa)

    except Exception as e:
        print(f"      ⚠️ Erro na varredura do site: {e}")

    bot_whatsapp.fechar_aba_segura(driver, driver.window_handles[0]) 
    return list(telefones_totais)

# ==============================================================================
# SISTEMA PRINCIPAL
# ==============================================================================

def iniciar_sistema():
    print("\n" + "="*60)
    print("🚀 SISTEMA DE VAGAS v2.3 - WHATSAPP PERSONALIZADO")
    print("="*60 + "\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # 1. WHATSAPP
    print("\n📲 PASSO 1: LOGIN WHATSAPP")
    driver.get("https://web.whatsapp.com")
    input(">>> Escaneie o QR Code e pressione ENTER aqui quando carregar...")

    # 2. APINFO
    print("\n📋 PASSO 2: NAVEGAÇÃO APINFO")
    driver.get("https://www.apinfo.com/apinfo/inc/list4.cfm")
    input(">>> Navegue até a lista desejada e pressione ENTER...")
    
    janela_lista = driver.current_window_handle
    print(f"✅ Lista fixada!")

    ja_logou = False
    pagina_atual = 1
    
    try:
        while True:
            print(f"\n📍 PROCESSANDO PÁGINA ATUAL")
            driver.switch_to.window(janela_lista)
            
            botoes = driver.find_elements(By.LINK_TEXT, "Envie seu currículo")
            if not botoes:
                print("⚠️ Nenhum botão encontrado. Recarregue a página.")
                input(">>> ENTER para tentar novamente...")
                continue

            lista_vagas = []
            for btn in botoes:
                link = btn.get_attribute("href")
                try:
                    elemento_pai = btn.find_element(By.XPATH, "./../..") 
                    texto_bruto = elemento_pai.text.replace("Envie seu currículo", "").strip()
                    descricao = texto_bruto if len(texto_bruto) > 10 else "Descrição indisponível"
                except:
                    descricao = "Descrição indisponível"
                if link:
                    lista_vagas.append({'link': link, 'desc': descricao})

            vagas_unicas = list({v['link']: v for v in lista_vagas}.values())
            print(f"Encontrei {len(vagas_unicas)} vagas.")

            for i, vaga in enumerate(vagas_unicas):
                driver.switch_to.window(janela_lista)
                link = vaga['link']
                desc_completa = vaga['desc']

                print(f"--------------------------------------------------")
                print(f"[Vaga {i+1}/{len(vagas_unicas)}] Analisando...")

                driver.execute_script(f"window.open('{link}', '_blank');")
                time.sleep(2)
                driver.switch_to.window(driver.window_handles[-1])
                janela_vaga = driver.current_window_handle

                if not ja_logou:
                    print("\n⚠️  PAUSA PARA LOGIN NA VAGA ⚠️")
                    print("1. Logue na vaga aberta.")
                    print("2. Volte aqui e dê ENTER.")
                    input(">>> ENTER APÓS LOGAR...")
                    ja_logou = True
                    janela_vaga = driver.window_handles[-1]
                    driver.switch_to.window(janela_vaga)
                    time.sleep(1)

                try:
                    texto_pagina = get_text_safe(driver, By.TAG_NAME, "body")
                    match_email = re.search(r'[\w\.-]+@[\w\.-]+', texto_pagina)
                    
                    if not match_email:
                        print("\n⚠️ E-mail sumiu. Logue novamente.")
                        input(">>> ENTER após relogar...")
                        driver.switch_to.window(driver.window_handles[-1])
                        texto_pagina = get_text_safe(driver, By.TAG_NAME, "body")
                        match_email = re.search(r'[\w\.-]+@[\w\.-]+', texto_pagina)

                    if match_email:
                        email_dest = match_email.group(0)
                        
                        if "staff@apinfo.com" in email_dest:
                            print("⛔ Bloqueio APInfo. Encerrando.")
                            driver.quit()
                            return

                        match_assunto = re.search(r'Assunto.*:(.*)', texto_pagina)
                        assunto_cod = match_assunto.group(1).strip() if match_assunto else "Vaga TI"

                        # Análise de Match
                        skills = analisar_aderencia(desc_completa)
                        
                        # --- PREPARAÇÃO DO TEXTO DO WHATSAPP ---
                        if skills:
                            # Se tiver skills compatíveis, cita elas
                            lista_skills = ", ".join(skills[:5]) # Pega as 5 primeiras pra não ficar gigante
                            msg_adicional = f"Vi que a vaga pede *{lista_skills}* e tenho experiência sólida nisso."
                        else:
                            # Se não achou skills específicas, manda genérico
                            msg_adicional = "Tenho experiência exatamente com o perfil da vaga."

                        txt_match = f"\n\nIdentifiquei aderência em:\n{chr(10).join(['- '+s for s in skills])}" if skills else ""
                        txt_salario = verifica_pedido_salario(desc_completa)
                        if txt_salario: print("   💰 Pede pretensão salarial.")

                        # E-mail
                        corpo = f"""
Olá,

Meu nome é {config.MEU_NOME}.
Eu me interessei pela vaga e fiz um script para enviar esse email pra voce.{txt_match}

Antes de mais nada, meu perfil é focado em Hard Skills como PHP/Laravel e Soft Skills de Gestão e Agilidade, possuo formação em Ciências da Computação e MBA em Gestão de Projetos.
Possuo experiencias em outras linguagens tambem como Python que to usando na criação desse script.
Segue meu CV em anexo.{txt_salario}

Fico à disposição para um bate-papo.

Atenciosamente,
{config.MEU_NOME}
(Enviado via Automação Python)

📱 Whatsapp: {config.TELEFONE_FORMATADO}
🔗 Clique para falar: {config.LINK_WHATSAPP_PESSOAL}
                        """
                        
                        print(f"   📧 Enviando e-mail para: {email_dest}...")
                        enviar_email_final(email_dest, assunto_cod, corpo)
                        
                        # WhatsApp
                        dominio = email_dest.split("@")[1].lower()
                        if dominio not in config.DOMINIOS_GENERICOS:
                            url_site = f"http://www.{dominio}"
                            
                            telefones = varrer_site_profundo(driver, url_site)
                            driver.switch_to.window(janela_vaga)
                            
                            if telefones:
                                # MENSAGEM DO WHATSAPP DINÂMICA AQUI
                                mensagem_zap = f"Olá, meu nome é {config.MEU_NOME}. Acabei de enviar meu CV para a vaga *{assunto_cod}*. {msg_adicional} Estou muito interessado! Obrigado."
                                
                                bot_whatsapp.processar_envios_whatsapp(driver, telefones, mensagem_zap, janela_vaga)
                        
                    else:
                        print("   ❌ Sem e-mail nesta vaga.")

                except Exception as e:
                    print(f"   Erro na vaga: {e}")

                finally:
                    bot_whatsapp.fechar_aba_segura(driver, janela_lista)
                    time.sleep(1)

            print("\n" + "█"*50)
            print("✅ PÁGINA FINALIZADA.")
            print("👉 Mude de página no Chrome e dê ENTER para continuar.")
            print("█"*50 + "\n")
            input(">>> AGUARDANDO COMANDO...")
            pagina_atual += 1

    except Exception as e:
        print(f"ERRO FATAL: {e}")

if __name__ == "__main__":
    iniciar_sistema()