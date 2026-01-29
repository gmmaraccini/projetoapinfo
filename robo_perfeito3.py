import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Importa a função de envio
from disparador import enviar_email_final

def iniciar_automacao():
    print("--- Iniciando Robô APInfo (Modo com Login Manual) ---")
    
    # Configuração simples (abre janela nova)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 1. ACESSA A LISTA
        url = "https://www.apinfo.com/apinfo/inc/list4.cfm" 
        print(f"Acessando: {url}")
        driver.get(url)
        time.sleep(3)

        # 2. PEGA OS LINKS
        print("Mapeando vagas...")
        botoes = driver.find_elements(By.LINK_TEXT, "Envie seu currículo")
        
        links_vagas = []
        for btn in botoes:
            link = btn.get_attribute("href")
            if link:
                links_vagas.append(link)
        
        # Remove duplicados e pega os primeiros 10
        links_vagas = list(set(links_vagas))[:10]
        print(f"Encontrei {len(links_vagas)} vagas.")

        # 3. LOOP DAS VAGAS
        for i, link in enumerate(links_vagas):
            print(f"--------------------------------------------------")
            print(f"[{i+1}/{len(links_vagas)}] Entrando na vaga...")
            
            driver.get(link)
            
            # =================================================================
            # 🛑 AQUI ESTÁ A TRAVA QUE VOCÊ PEDIU (SÓ NA PRIMEIRA VAGA)
            # =================================================================
            if i == 0:
                print("\n" + "█"*60)
                print("⚠️  PAUSA OBRIGATÓRIA PARA LOGIN  ⚠️")
                print("1. Vá no navegador agora.")
                print("2. Faça o LOGIN e resolva o CAPTCHA.")
                print("3. Espere a página carregar e mostrar os dados da vaga (Email/Assunto).")
                print("4. Volte aqui e aperte ENTER para continuar.")
                print("█"*60 + "\n")
                input(">>> APERTE ENTER AQUI DEPOIS DE LOGAR...")
                print("... Retomando automação ...")
            else:
                # Nas próximas vagas, ele só espera um pouquinho (já vai estar logado)
                time.sleep(2) 

            # =================================================================
            # DAQUI PRA BAIXO SEGUE NORMAL (LÊ E ENVIA)
            # =================================================================

            # Pega o texto da página (agora já logado)
            texto_pagina = driver.find_element(By.TAG_NAME, "body").text

            match_email = re.search(r'[\w\.-]+@[\w\.-]+', texto_pagina)
            match_assunto = re.search(r'Assunto.*:(.*)', texto_pagina)

            if match_email:
                email_destino = match_email.group(0)
                assunto_cod = match_assunto.group(1).strip() if match_assunto else f"Vaga DEV PHP"
                
                print(f"   ✅ ALVO: {email_destino}")
                print(f"   📝 REF: {assunto_cod}")

                corpo_email = f"""
                Olá,
                
                Vi o anúncio da vaga no APInfo (Cód: {assunto_cod}) e tenho interesse.
                Sou desenvolvedor Sênior com 10 anos de experiência em PHP/Laravel.
                Segue CV anexo.
                
                Att,
                Gabriel Maraccini
                """

                # Envia
                enviou = enviar_email_final(email_destino, assunto_cod, corpo_email)
                
                if enviou:
                    print("   🚀 Enviado!")
                else:
                    print("   ❌ Erro no envio.")
            else:
                print("   ⚠️ Pulei: Nenhum email na tela (O login funcionou?)")

    except Exception as e:
        print(f"ERRO: {e}")
    
    finally:
        print("Fim.")
        # driver.quit() # Mantive comentado pra não fechar na sua cara

if __name__ == "__main__":
    iniciar_automacao()