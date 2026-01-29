import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def enviar_email_final(destinatario, assunto, corpo_texto, arquivo_anexo="cv_gabriel_maraccini.docx"):
    # --- SUAS CONFIGURAÇÕES QUE FUNCIONARAM NO TESTE ---
    meu_email = "gmmaraccini@gmail.com"
    minha_senha = "ozpsxfcdttulkunc" # A senha que deu sucesso!
    
    msg = MIMEMultipart()
    msg['From'] = meu_email
    msg['To'] = destinatario
    msg['Subject'] = assunto

    msg.attach(MIMEText(corpo_texto, 'plain'))

    # Lógica de anexo validada
    if os.path.exists(arquivo_anexo):
        try:
            with open(arquivo_anexo, "rb") as anexo:
                parte = MIMEBase('application', 'octet-stream')
                parte.set_payload(anexo.read())
            encoders.encode_base64(parte)
            parte.add_header(
                "Content-Disposition",
                f"attachment; filename= {arquivo_anexo}",
            )
            msg.attach(parte)
            print(f"   📎 Anexo '{arquivo_anexo}' preparado.")
        except Exception as e:
            print(f"   ⚠️ Erro no anexo: {e}")
    else:
        print(f"   ⚠️ AVISO: '{arquivo_anexo}' não encontrado. Enviando sem anexo.")

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(meu_email, minha_senha)
        server.sendmail(meu_email, destinatario, msg.as_string())
        server.quit()
        print(f"   ✅ E-mail enviado com sucesso para: {destinatario}")
        return True
    except Exception as e:
        print(f"   ❌ ERRO DE ENVIO: {e}")
        return False