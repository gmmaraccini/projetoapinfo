import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Importa o disparador configurado
from disparador import enviar_email_final

# ==============================================================================
# DADOS DO CANDIDATO
# ==============================================================================
MEU_NOME = "Gabriel Maraccini"
LINK_WHATSAPP = "https://wa.me/5511984314366"
TELEFONE_FORMATADO = "(11) 98431-4366"

# Gatilhos para incluir pretensão salarial
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
    """Verifica se a vaga pede pretensão salarial"""
    desc_lower = descricao_vaga.lower()
    if any(termo in desc_lower for termo in TERMOS_SALARIO):
        return "\nPretensão salarial: R$ 8.000,00 ou a combinar dependendo dos benefícios."
    return ""

def iniciar_automacao():
    print("\n" + "="*60)
    print("🚀 ROBÔ APINFO - MODO ATIVO (ENVIANDO E-MAILS REAIS)")
    print("="*60 + "\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
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

            if not vagas_unicas:
                print("⚠️ Nenhuma vaga encontrada.")

            janela_lista = driver.current_window_handle

            for i, vaga in enumerate(vagas_unicas):
                link = vaga['link']
                desc_completa = vaga['desc']

                print(f"--------------------------------------------------")
                print(f"[Pg {pagina_atual} | Vaga {i+1}] Analisando...")

                driver.execute_script(f"window.open('{link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(3) # Aumentei um pouco para evitar bloqueio rápido 

                if not ja_logou:
                    print("\n" + "█"*60)
                    print("⚠️  PAUSA PARA LOGIN  ⚠️")
                    print("1. Logue na vaga aberta.")
                    print("2. Certifique-se de ver o email.")
                    print("3. Volte aqui e dê ENTER.")
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
                        match_assunto = re.search(r'Assunto.*:(.*)', texto_pagina)
                        assunto_cod = match_assunto.group(1).strip() if match_assunto else "Vaga PHP"

                        # === INTELIGÊNCIA ===
                        skills_encontradas = analisar_aderencia(desc_completa)
                        if skills_encontradas:
                            lista_skills_txt = "\n".join([f"- {s}" for s in skills_encontradas])
                            texto_match = f"\n\nCruzando as informações da vaga com meu currículo, identifiquei total aderência nos seguintes pontos:\n{lista_skills_txt}"
                        else:
                            texto_match = ""

                        texto_salario = verifica_pedido_salario(desc_completa)
                        if texto_salario:
                            print("   💰 Vaga pede pretensão salarial.")

                        # === MONTAGEM DO E-MAIL ===
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
                        
                        # === ENVIO REAL ===
                        enviar_email_final(email_dest, assunto_cod, corpo)

                    else:
                        print("   ❌ Sem e-mail nesta vaga.")

                except Exception as e:
                    print(f"   Erro: {e}")

                driver.close()
                driver.switch_to.window(janela_lista)
                time.sleep(2) # Pausa estratégica para evitar bloqueio 173

            # PAGINAÇÃO MANUAL
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