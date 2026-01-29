import smtplib
from email.mime.text import MIMEText

def testar_conexao():
    print("--- TESTE DE LOGIN GMAIL ---")
    
    # SEUS DADOS
    email = "gmmaraccini@gmail.com"
    
    # Tentei com e sem espaços. O ideal para o Python é SEM espaços.
    # Senha que você passou: ozps xfcd ttul kunc
    senha_app = "ozpsxfcdttulkunc" 
    
    print(f"Tentando conectar como: {email}")
    
    try:
        # Tenta conectar no servidor
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Tenta o LOGIN
        print("Enviando credenciais...")
        server.login(email, senha_app)
        print("✅ SUCESSO! Login aceito.")
        
        # Tenta enviar um email para você mesmo
        msg = MIMEText("Se você recebeu isso, a senha funciona.")
        msg['Subject'] = "Teste de Senha Python"
        msg['From'] = email
        msg['To'] = email
        
        server.sendmail(email, email, msg.as_string())
        print("✅ E-mail de teste enviado para sua própria caixa de entrada.")
        
        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ ERRO 535: O Google recusou a senha.")
        print("Possíveis causas:")
        print("1. A senha de App foi revogada ou digitada errada.")
        print("2. O e-mail 'gmmaraccini@gmail.com' não é o mesmo que gerou a senha.")
        print("3. Você está usando a senha normal do Gmail (não pode).")
    except Exception as e:
        print(f"\n❌ OUTRO ERRO: {e}")

if __name__ == "__main__":
    testar_conexao()