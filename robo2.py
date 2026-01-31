import re
import time
import urllib.parse
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Importa o disparador configurado
from disparador import enviar_email_final

# ==============================================================================
# CONFIGURAÇÕES DO USUÁRIO
# ==============================================================================
MEU_NOME = "Gabriel Maraccini"
LINK_WHATSAPP = "https://wa.me/5511984314366"
TELEFONE_FORMATADO = "(11) 98431-4366"

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

def verificar_sincronizacao_whatsapp():
    """
    Abre o WhatsApp Web e aguarda confirmação manual do usuário
    para garantir que o envio posterior não falhe.
    """
    print("\n" + "█"*60)
    print("📲 VERIFICAÇÃO DE WHATSAPP")
    print("Vou abrir o WhatsApp Web agora para testar a conexão.")
    print("█"*60)
    
    webbrowser.open("https://web.whatsapp.com")
    
    print("\n⚠️  ATENÇÃO: O WhatsApp abriu e carregou suas conversas?")
    print("   [1] Se apareceu o QR CODE: Escaneie agora com seu celular.")
    print("   [2] Se já apareceram as conversas: Tudo pronto.")
    
    # Trava o script aqui até você apertar Enter
    input("\n>>> Quando estiver sincronizado e pronto, PRESSIONE ENTER para começar...")
    print("✅ WhatsApp Confirmado! Iniciando automação...\n")


def analisar_aderencia(descricao_vaga):
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
    desc_lower = descricao_vaga.lower()
    if any(termo in desc_lower for termo in TERMOS_SALARIO):
        return "\nPretensão salarial: R$ 8.000,00 ou a combinar dependendo dos benefícios."
    return ""

def buscar_e_contatar_whatsapp(driver, email_empresa, titulo_vaga):
    try:
        dominio = email_empresa.split("@")[1].lower()
        
        if dominio in DOMINIOS_GENERICOS:
            print(f"   ℹ️ Domínio genérico ({dominio}). Pulando busca de site.")
            return

        url_empresa = f"http://www.{dominio}"
        print(f"\n   🌍 Visitando site da empresa: {url_empresa}...")

        driver.execute_script(f"window.open('{url_empresa}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        
        driver.set_page_load_timeout(15)
        try:
            time.sleep(4)
            texto_site = driver.find_element(By.TAG_NAME, "body").text
        except:
            print("   ⚠️ Site demorou. Tentando ler o que carregou...")
            try:
                texto_site = driver.find_element(By.TAG_NAME, "body").text
            except:
                texto_site = ""

        padrao_tel = r'(?:(?:\+|00)?(55)\s?)?(?:\(?([1-9][0-9])\)?\s?)?(?:((?:9\d|[2-9])\d{3})\-?(\d{4}))'
        
        def extrair_telefones(texto):
            encontrados = re.findall(padrao_tel, texto)
            lista = []
            for match in encontrados:
                ddd, p1, p2 = match[1], match[2], match[3]
                numero_completo = f"{ddd}{p1}{p2}"
                if ddd and len(numero_completo) >= 11 and p1.startswith('9'): 
                    lista.append(numero_completo)
            return lista

        telefones_validos = extrair_telefones(texto_site)
        
        if not telefones_validos:
            print("   ⚠️ Nenhum celular na Home. Buscando 'Fale Conosco'...")
            try:
                xpaths = [
                    "//a[contains(translate(text(), 'C', 'c'), 'contato')]",
                    "//a[contains(translate(text(), 'F', 'f'), 'fale')]",
                    "//a[contains(translate(text(), 'T', 't'), 'trabalhe')]",
                    "//a[contains(@href, 'contato')]"
                ]
                for xpath in xpaths:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    if elementos:
                        try:
                            elementos[0].click()
                            time.sleep(4)
                            texto_contato = driver.find_element(By.TAG_NAME, "body").text
                            telefones_validos.extend(extrair_telefones(texto_contato))
                            break
                        except:
                            pass
            except:
                pass

        telefones_validos = list(set(telefones_validos))

        if telefones_validos:
            print(f"   📱 Celulares encontrados: {telefones_validos}")
            
            msg_texto = f"Bom dia, meu nome é {MEU_NOME}. Enviei um currículo para a vaga '{titulo_vaga}'. Fiquei muito interessado e gostaria que vocês avaliassem meu currículo. Obrigado =)"
            msg_encoded = urllib.parse.quote(msg_texto)

            for fone in telefones_validos:
                link_wa = f"https://web.whatsapp.com/send?phone=55{fone}&text={msg_encoded}"
                print(f"   💬 Preparando WhatsApp para: {fone}")
                
                # Abre no Chrome padrão do usuário
                webbrowser.open_new_tab(link_wa)
                time.sleep(1.5) 
        else:
            print("   ❌ Nenhum celular encontrado no site.")

        driver.close()
        
    except Exception as e:
        print(f"   ⚠️ Erro ao navegar no site da empresa: {e}")
        try:
            if len(driver.window_handles) > 2:
                driver.close()
        except:
            pass

def iniciar_automacao():
    # === PASSO 1: VERIFICAÇÃO DE WHATSAPP ===
    verificar_sincronizacao_whatsapp()
    
    # === PASSO 2: INICIA O ROBÔ DE VAGAS ===
    print("\n" + "="*60)
    print("🚀 ROBÔ APINFO - MODO COMPLETO (EMAIL + WHATSAPP)")
    print("="*60 + "\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    ja_logou = False
    pagina_atual = 1
    limite_paginas = 10 

    try:
        url = "https://www.apinfo.com/apinfo/inc/list4.cfm" 
        print(f"Acessando: {url}")
        driver.get(url)
        time.sleep(3)

        while pagina_atual <= limite_paginas:
            print(f"\n📍 PROCESSANDO PÁGINA {pagina_atual}")
            
            botoes = driver.find_elements(By.LINK_TEXT, "Envie seu currículo")
            
            lista_vagas = []
            for btn in botoes:
                link = btn.get_attribute("href")
                try:
                    elemento_pai = btn.find_element(By.XPATH, "./../..") 
                    texto_bruto = elemento_pai.text.replace("Envie seu currículo", "").strip()
                    descricao_full = texto_bruto if len(texto_bruto) > 10 else "Descrição não capturada"
                    if descricao_full == "Descrição não capturada":
                         elemento_avo = btn.find_element(By.XPATH, "./../../..")
                         descricao_full = elemento_avo.text.replace("Envie seu currículo", "").strip()
                except:
                    descricao_full = "Descrição não capturada"

                if link:
                    lista_vagas.append({'link': link, 'desc': descricao_full})

            vagas_unicas = list({v['link']: v for v in lista_vagas}.values())
            print(f"Encontrei {len(vagas_unicas)} vagas.")

            janela_lista = driver.current_window_handle

            for i, vaga in enumerate(vagas_unicas):
                link = vaga['link']
                desc_completa = vaga['desc']

                print(f"--------------------------------------------------")
                print(f"[Pg {pagina_atual} | Vaga {i+1}] Analisando...")

                driver.execute_script(f"window.open('{link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
                janela_vaga = driver.current_window_handle
                
                time.sleep(3) 

                if not ja_logou:
                    print("\n" + "█"*60)
                    print("⚠️  PAUSA PARA LOGIN APINFO ⚠️")
                    print("1. Logue na vaga aberta.")
                    print("2. Volte aqui e dê ENTER.")
                    print("█"*60 + "\n")
                    input(">>> ENTER APÓS LOGAR...")
                    ja_logou = True
                    time.sleep(1)

                try:
                    texto_pagina = driver.find_element(By.TAG_NAME, "body").text
                    match_email = re.search(r'[\w\.-]+@[\w\.-]+', texto_pagina)
                    
                    if not match_email:
                        print("\n⚠️ E-mail não visível. O login pode ter expirado.")
                        input(">>> Faça login novamente e dê ENTER...")
                        texto_pagina = driver.find_element(By.TAG_NAME, "body").text
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
                        if skills_encontradas:
                            lista_skills_txt = "\n".join([f"- {s}" for s in skills_encontradas])
                            texto_match = f"\n\nCruzando as informações da vaga com meu currículo, identifiquei total aderência nos seguintes pontos:\n{lista_skills_txt}"
                        else:
                            texto_match = ""

                        texto_salario = verifica_pedido_salario(desc_completa)
                        if texto_salario:
                            print("   💰 Vaga pede pretensão salarial.")

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
                        
                        buscar_e_contatar_whatsapp(driver, email_dest, assunto_cod)

                    else:
                        print("   ❌ Sem e-mail nesta vaga.")

                except Exception as e:
                    print(f"   Erro: {e}")

                try:
                    if driver.current_window_handle == janela_vaga:
                        driver.close()
                except:
                    pass
                
                driver.switch_to.window(janela_lista)
                time.sleep(2) 

            print("\n" + "█"*50)
            print("✅ FIM DA PÁGINA.")
            print(f"👉 CLIQUE NA PÁGINA {pagina_atual + 1} NO CHROME.")
            print("█"*50 + "\n")
            input(f">>> ENTER QUANDO A PÁGINA {pagina_atual + 1} CARREGAR...")
            pagina_atual += 1

    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        print("Fim.")

if __name__ == "__main__":
    iniciar_automacao()