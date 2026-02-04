import re
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Importa o disparador configurado
from disparador import enviar_email_final

# ==============================================================================
# CONFIGURAÇÕES DO USUÁRIO
# ==============================================================================
MEU_NOME = "Gabriel Maraccini"
LINK_WHATSAPP = "https://wa.me/5511984314366"
TELEFONE_FORMATADO = "(11) 98431-4366"
DDD_PADRAO = "11" 

DOMINIOS_GENERICOS = [
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com.br", 
    "yahoo.com", "bol.com.br", "uol.com.br", "terra.com.br", 
    "ig.com.br", "icloud.com", "apinfo.com"
]

TERMOS_SALARIO = [
    "pretensão", "pretensao", "salarial", "salário", "salario", 
    "remuneração", "remuneracao", "faixa", "enviar valor"
]

HARD_SKILLS = [
    "PHP", "Laravel", "Yii", "Javascript", "TypeScript", "Node", "React", "React Native",
    "MySQL", "SQL", "PostgreSQL", "Oracle", "Redis", "SQS", "RabbitMQ",
    "Docker", "Kubernetes", "AWS", "Cloud", "Linux", "Nginx", "Apache",
    "Git", "GitHub", "GitLab", "CI/CD", "Jenkins", "DevOps",
    "API", "REST", "SOAP", "Microserviços", "PWA", "Mobile",
    "Python", "C#", "Java", "JQuery", "CSS", "HTML"
]

SOFT_SKILLS = [
    "Scrum", "Kanban", "Agile", "Ágil", "Jira", "Trello",
    "Gestão de Equipe", "Liderança", "Documentação", "Refatoração",
    "Engenharia Reversa", "Mentoria", "Resolução de Problemas",
    "Inteligência Emocional", "Comunicação", "Inglês", "Espanhol"
]

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def get_text_safe(driver, by, value):
    try:
        element = driver.find_element(by, value)
        if element: return element.text
    except: pass
    return ""

def fechar_aba_segura(driver, janela_para_voltar):
    """
    Fecha a aba atual (se não for a última) e volta para a janela especificada.
    """
    try:
        # Se tiver mais de 1 aba aberta, fecha a atual
        if len(driver.window_handles) > 1:
            driver.close()
    except Exception:
        pass 
    
    # Tenta focar na janela de destino (Vaga ou Lista)
    try:
        driver.switch_to.window(janela_para_voltar)
    except:
        # Se a janela de destino sumiu, pega a última disponível
        if len(driver.window_handles) > 0:
            driver.switch_to.window(driver.window_handles[-1])

def analisar_aderencia(descricao_vaga):
    if not descricao_vaga: return []
    desc_lower = descricao_vaga.lower()
    matches = []
    for skill in HARD_SKILLS:
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', desc_lower):
            matches.append(skill)
    for skill in SOFT_SKILLS:
        if skill.lower() in desc_lower:
            matches.append(skill)
    return sorted(list(set(matches)))

def verifica_pedido_salario(descricao_vaga):
    if not descricao_vaga: return ""
    desc_lower = descricao_vaga.lower()
    if any(termo in desc_lower for termo in TERMOS_SALARIO):
        return "\nPretensão salarial: R$ 8.000,00 ou a combinar dependendo dos benefícios."
    return ""

def extrair_celulares(texto):
    if not texto: return []
    padrao = r'(?:\(?([1-9][0-9])\)?\s?)?(9\d{4})[\s-]?(\d{4})'
    encontrados = re.findall(padrao, texto)
    lista_formatada = []
    for match in encontrados:
        ddd, parte1, parte2 = match[0], match[1], match[2]
        celular_limpo = f"{parte1}{parte2}"
        if ddd:
            numero_final = f"55{ddd}{celular_limpo}"
        else:
            numero_final = f"55{DDD_PADRAO}{celular_limpo}"
        lista_formatada.append(numero_final)
    return list(set(lista_formatada))

def buscar_e_contatar_whatsapp(driver, email_empresa, titulo_vaga, janela_anterior_vaga):
    """
    Abre o WhatsApp, envia e fecha, voltando para a janela da VAGA (não da lista).
    """
    try:
        if not email_empresa or "@" not in email_empresa: return
        dominio = email_empresa.split("@")[1].lower()
        if dominio in DOMINIOS_GENERICOS:
            print(f"   ℹ️ Domínio genérico ({dominio}). Pulando busca de site.")
            return

        url_home = f"http://www.{dominio}"
        print(f"\n   🌍 Iniciando varredura no site: {url_home}...")

        telefones_encontrados = set()

        # 1. ANALISAR A HOME
        driver.execute_script(f"window.open('{url_home}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        
        driver.set_page_load_timeout(20)
        try:
            time.sleep(4)
            texto_home = get_text_safe(driver, By.TAG_NAME, "body")
            telefones_home = extrair_celulares(texto_home)
            telefones_encontrados.update(telefones_home)
            if telefones_home:
                print(f"      -> Home: Encontrei {len(telefones_home)} números.")
        except:
            print("      ⚠️ Erro ao ler a Home.")

        # 2. BUSCAR LINKS INTERNOS
        termos_busca = ['contato', 'fale', 'trabalhe', 'contact', 'work']
        links_para_visitar = []
        try:
            elementos_a = driver.find_elements(By.TAG_NAME, "a")
            for elem in elementos_a:
                href = elem.get_attribute("href")
                try: texto_link = elem.text.lower()
                except: texto_link = ""
                
                if href and any(termo in texto_link or termo in href.lower() for termo in termos_busca):
                    if dominio in href and "mailto" not in href and "whatsapp" not in href:
                        links_para_visitar.append(href)
            
            links_para_visitar = list(set(links_para_visitar))[:3]
            
            for link_interno in links_para_visitar:
                try:
                    print(f"         Visitando: {link_interno}...")
                    driver.execute_script(f"window.open('{link_interno}', '_blank');")
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(3)
                    
                    texto_pag = get_text_safe(driver, By.TAG_NAME, "body")
                    tels_pag = extrair_celulares(texto_pag)
                    if tels_pag:
                        print(f"         + {len(tels_pag)} novos números.")
                        telefones_encontrados.update(tels_pag)
                    
                    fechar_aba_segura(driver, driver.window_handles[-1]) # Fecha e volta pra home
                except:
                    fechar_aba_segura(driver, driver.window_handles[-1])

        except Exception as e:
            print(f"      Erro ao buscar links internos: {e}")

        # Fecha a aba da empresa e volta para a janela da VAGA
        fechar_aba_segura(driver, janela_anterior_vaga)

        # 3. DISPARAR WHATSAPP
        lista_final = list(telefones_encontrados)
        if lista_final:
            print(f"   📱 TELEFONES ENCONTRADOS (Formatados): {lista_final}")
            msg_texto = f"Bom dia, meu nome é {MEU_NOME}. Enviei um currículo para a vaga '{titulo_vaga}'. Fiquei muito interessado e gostaria que vocês avaliassem meu currículo. Obrigado =)"
            msg_encoded = urllib.parse.quote(msg_texto)

            for fone in lista_final:
                link_wa = f"https://web.whatsapp.com/send?phone={fone}&text={msg_encoded}"
                print(f"   💬 Abrindo WhatsApp para: {fone}...")
                
                driver.execute_script(f"window.open('{link_wa}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
                
                try:
                    # ESPERA E ENVIA (IGUAL AO SCRIPT DE NATAL)
                    print("      -> Aguardando carregamento (15s)...")
                    time.sleep(15) 

                    # Verifica erro de número
                    try:
                        aviso = driver.find_elements(By.XPATH, '//*[contains(text(), "inválido") or contains(text(), "invalid")]')
                        if aviso and aviso[0].is_displayed():
                            print(f"      ❌ Número Inválido.")
                            fechar_aba_segura(driver, janela_anterior_vaga)
                            continue 
                    except: pass

                    # Tenta ENVIAR
                    print("      -> Tentando enviar...")
                    enviado = False
                    
                    try:
                        # Tenta botão
                        btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='send']"))
                        )
                        btn.click()
                        enviado = True
                        print("      ✅ Enviado (Clique no Botão).")
                    except:
                        # Tenta Enter na caixa
                        try:
                            caixa = driver.find_element(By.CSS_SELECTOR, '#main footer div[contenteditable="true"]')
                            caixa.send_keys(Keys.ENTER)
                            enviado = True
                            print("      ✅ Enviado (Enter na Caixa).")
                        except:
                            print("      ⚠️ Não consegui achar botão nem caixa.")

                    if enviado:
                        time.sleep(5)

                except Exception as e:
                    print(f"      ❌ Erro no Whats: {e}")
                
                # FECHA O WHATSAPP E VOLTA PRA VAGA
                fechar_aba_segura(driver, janela_anterior_vaga)
                
        else:
            print("   ❌ Nenhum celular encontrado no site.")
        
    except Exception as e:
        print(f"   ⚠️ Erro geral na navegação da empresa: {e}")
        try: driver.switch_to.window(janela_anterior_vaga)
        except: pass

def iniciar_automacao():
    print("\n" + "="*60)
    print("🚀 ROBÔ APINFO - VERSÃO FINAL CHECK-MATE")
    print("="*60 + "\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # 1. WHATSAPP
    print("\n" + "█"*60)
    print("📲 PASSO 1: WHATSAPP WEB")
    print("Vou abrir o WhatsApp. Escaneie o QR Code se necessário.")
    print("█"*60)
    
    driver.get("https://web.whatsapp.com")
    input(">>> DEPOIS QUE CARREGAR AS CONVERSAS, DÊ ENTER...")

    # 2. LISTA
    print("\n" + "█"*60)
    print("📋 PASSO 2: ESCOLHA A LISTA DE VAGAS")
    print("Vou abrir a APInfo. Navegue até a lista desejada.")
    print("█"*60)

    driver.get("https://www.apinfo.com/apinfo/inc/list4.cfm")
    
    input(">>> QUANDO ESTIVER VENDO A LISTA DE VAGAS DESEJADA, DÊ ENTER...")
    
    janela_lista = driver.current_window_handle
    print(f"✅ Janela da Lista fixada!")

    ja_logou = False
    pagina_atual = 1
    limite_paginas = 100 

    try:
        while pagina_atual <= limite_paginas:
            print(f"\n📍 PROCESSANDO PÁGINA ATUAL")
            
            driver.switch_to.window(janela_lista)
            botoes = driver.find_elements(By.LINK_TEXT, "Envie seu currículo")
            
            if not botoes:
                print("⚠️ Não achei botões. Tente recarregar.")
                input(">>> Dê ENTER para tentar novamente...")
                continue

            lista_vagas = []
            for btn in botoes:
                link = btn.get_attribute("href")
                try:
                    elemento_pai = btn.find_element(By.XPATH, "./../..") 
                    texto_bruto = elemento_pai.text.replace("Envie seu currículo", "").strip()
                    descricao_full = texto_bruto if len(texto_bruto) > 10 else "Descrição não capturada"
                except:
                    descricao_full = "Descrição não capturada"
                if link:
                    lista_vagas.append({'link': link, 'desc': descricao_full})

            # Remove duplicados
            vagas_unicas = list({v['link']: v for v in lista_vagas}.values())
            print(f"Encontrei {len(vagas_unicas)} vagas nesta página.")

            for i, vaga in enumerate(vagas_unicas):
                driver.switch_to.window(janela_lista)
                
                link = vaga['link']
                desc_completa = vaga['desc']

                print(f"--------------------------------------------------")
                print(f"[Vaga {i+1}/{len(vagas_unicas)}] Analisando...")

                # Abre a VAGA
                driver.execute_script(f"window.open('{link}', '_blank');")
                time.sleep(2)
                driver.switch_to.window(driver.window_handles[-1])
                janela_vaga = driver.current_window_handle

                # Login Manual
                if not ja_logou:
                    print("\n" + "█"*60)
                    print("⚠️  PAUSA PARA LOGIN NA VAGA ⚠️")
                    print("1. Logue na vaga aberta.")
                    print("2. Volte aqui e dê ENTER.")
                    print("█"*60 + "\n")
                    input(">>> ENTER APÓS LOGAR...")
                    ja_logou = True
                    janela_vaga = driver.window_handles[-1]
                    driver.switch_to.window(janela_vaga)
                    time.sleep(1)

                try:
                    texto_pagina = get_text_safe(driver, By.TAG_NAME, "body")
                    match_email = re.search(r'[\w\.-]+@[\w\.-]+', texto_pagina)
                    
                    if not match_email:
                        print("\n⚠️ E-mail não visível. O login pode ter expirado.")
                        input(">>> Faça login novamente e dê ENTER...")
                        driver.switch_to.window(driver.window_handles[-1]) 
                        janela_vaga = driver.current_window_handle
                        texto_pagina = get_text_safe(driver, By.TAG_NAME, "body")
                        match_email = re.search(r'[\w\.-]+@[\w\.-]+', texto_pagina)

                    if match_email:
                        email_dest = match_email.group(0)
                        
                        if "staff@apinfo.com" in email_dest:
                            print("\n" + "⛔"*30)
                            print("ALERTA: BLOQUEIO DO APINFO!")
                            driver.quit() 
                            return 

                        match_assunto = re.search(r'Assunto.*:(.*)', texto_pagina)
                        assunto_cod = match_assunto.group(1).strip() if match_assunto else "Vaga PHP"

                        skills_encontradas = analisar_aderencia(desc_completa)
                        texto_match = f"\n\nCruzando as informações da vaga com meu currículo, identifiquei total aderência nos seguintes pontos:\n{chr(10).join(['- '+s for s in skills_encontradas])}" if skills_encontradas else ""

                        texto_salario = verifica_pedido_salario(desc_completa)
                        if texto_salario: print("   💰 Vaga pede pretensão salarial.")

                        corpo = f"""
Olá,

Meu nome é {MEU_NOME}.
Eu me interessei pela vaga e fiz um script para enviar esse email pra voce.{texto_match}

Antes de mais nada, meu perfil é focado em Hard Skills como PHP/Laravel e Soft Skills de Gestão e Agilidade, possuo formação em Ciências da Computação e MBA em Gestão de Projetos.
Possuo experiencias em outras linguagens tambem como Python que to usando na criação desse script.
Segue meu CV em anexo para detalhar minha experiência.{texto_salario}

Fico à disposição para um bate-papo.

Atenciosamente,
{MEU_NOME}
(Enviado via Automação Python)

📱 Whatsapp: {TELEFONE_FORMATADO}
🔗 Clique para falar: {LINK_WHATSAPP}
                        """
                        
                        print(f"   📧 Enviando para: {email_dest}...")
                        enviar_email_final(email_dest, assunto_cod, corpo)
                        
                        # --- PULO DO GATO ---
                        # Passamos 'janela_vaga' (filha) e não 'janela_lista' (mãe)
                        # Assim o WhatsApp fecha e volta pra vaga. E a vaga fecha e volta pra lista.
                        buscar_e_contatar_whatsapp(driver, email_dest, assunto_cod, janela_vaga)
                    else:
                        print("   ❌ Sem e-mail nesta vaga.")
                
                except Exception as e:
                    print(f"   Erro no processo da vaga: {e}")
                
                finally:
                    # Agora sim, fechamos a aba da vaga com segurança
                    # e voltamos para a lista principal
                    fechar_aba_segura(driver, janela_lista)
                    time.sleep(1) 

            print("\n" + "█"*50)
            print("✅ FIM DAS VAGAS DESTA PÁGINA.")
            print(f"👉 AGORA, LÁ NO CHROME, CLIQUE NA PRÓXIMA PÁGINA (Ex: Pg 2, 3...)")
            print("█"*50 + "\n")
            input(f">>> QUANDO A NOVA PÁGINA CARREGAR, DÊ ENTER AQUI...")
            pagina_atual += 1

    except Exception as e:
        print(f"ERRO GERAL: {e}")
    finally:
        print("Fim.")

if __name__ == "__main__":
    iniciar_automacao()