# INÍCIO DO SCRIPT

import oci
import time
import random
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta, timezone
import os

# Configurações
RETENCAO_DIAS = 15
COMPARTMENT_NAME = "LinuxBancoDados"
LOG_DIR = "./logs"
ENABLE_EMAIL_ALERTS = False #use True or False

# Configurações de e-mail
EMAIL_SERVER = "smtp.seuprovedor.com"
EMAIL_PORT = 587
EMAIL_SENDER = "seuemail@dominio.com"
EMAIL_PASSWORD = "sua_senha"
EMAIL_RECIPIENTS = ["admin1@exemplo.com", "admin2@exemplo.com"]

# Cria diretório de logs
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_filename = os.path.join(LOG_DIR, f"Backup_BootVolume_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_filename),
    logging.StreamHandler()
])

# OCI Config
config = oci.config.from_file()
config['region'] = 'sa-saopaulo-1'
block_storage = oci.core.BlockstorageClient(config)
identity = oci.identity.IdentityClient(config)

def enviar_email_alerta(log_filename):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = ", ".join(EMAIL_RECIPIENTS)
        msg['Subject'] = "Erro Crítico no Script de Backup"
        msg.attach(MIMEText("Ocorreu um erro crítico durante a execução do script de backup. Veja o log em anexo.", 'plain'))

        with open(log_filename, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(log_filename)}")
            msg.attach(part)

        server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())
        server.quit()
        logging.info("Email de alerta enviado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao enviar email de alerta: {str(e)}")

def get_compartment_id():
    compartments = oci.pagination.list_call_get_all_results(
        identity.list_compartments,
        config['tenancy'],
        compartment_id_in_subtree=True
    ).data
    for comp in compartments:
        if comp.name == COMPARTMENT_NAME:
            return comp.id
    raise ValueError(f"Compartment {COMPARTMENT_NAME} não encontrado")

def delete_old_backups(boot_volume_id):
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=RETENCAO_DIAS)
    backups = block_storage.list_boot_volume_backups(
        compartment_id=compartment_id,
        boot_volume_id=boot_volume_id
    ).data
    for backup in backups:
        backup_time = backup.time_created.replace(tzinfo=timezone.utc)
        if backup_time < cutoff_time:
            if backup.lifecycle_state == "AVAILABLE":
                try:
                    block_storage.delete_boot_volume_backup(backup.id)
                    logging.info(f"🗑️ Backup excluído: {backup.display_name} ({backup_time.date()})")
                except Exception as e:
                    logging.error(f"❌ Erro ao excluir {backup.display_name}: {str(e)}")
            else:
                logging.warning(f"⏳ Backup ignorado (estado {backup.lifecycle_state}): {backup.display_name}")

def criar_backup_com_backoff(boot_volume, max_retentativas=5):
    espera = 1
    backup_name = f"BootBackup-{boot_volume.display_name}-{datetime.now(timezone.utc).strftime('BKPAUTCITEL-%Y%m%d-%H%M')}"
    backup_details = oci.core.models.CreateBootVolumeBackupDetails(
        boot_volume_id=boot_volume.id,
        display_name=backup_name,
        type="FULL"
    )
    for tentativa in range(max_retentativas):
        try:
            block_storage.create_boot_volume_backup(backup_details)
            logging.info(f"✅ Backup criado: {backup_name}")
            return True
        except oci.exceptions.ServiceError as e:
            if e.status == 429 and "TooManyRequests" in str(e):
                logging.warning(f"⚠️ Tentativa {tentativa+1}: Limite de requisições. Aguardando {espera}s...")
                time.sleep(espera + random.uniform(0, 5))
                espera *= 2
            else:
                logging.error(f"❌ Erro ao criar backup: {str(e)}")
                return False
        except Exception as e:
            logging.error(f"❌ Erro inesperado: {str(e)}")
            return False
    return False

def main():
    global compartment_id
    compartment_id = get_compartment_id()
    falhas = []
    boot_volumes = oci.pagination.list_call_get_all_results(
        block_storage.list_boot_volumes,
        compartment_id=compartment_id
    ).data
    for bv in boot_volumes:
        if bv.lifecycle_state != "AVAILABLE":
            continue
        logging.info(f"\n🔍 Processando boot volume: {bv.display_name}")
        sucesso = criar_backup_com_backoff(bv)
        if not sucesso:
            falhas.append(bv)
        delete_old_backups(bv.id)
    if falhas:
        logging.info("\n🔁 Tentando novamente os backups que falharam...")
        for bv in falhas:
            logging.info(f"\n🔄 Reprocessando: {bv.display_name}")
            criar_backup_com_backoff(bv)

if __name__ == "__main__":
    try:
        main()
        logging.info("\n✅ Execução concluída com sucesso")
    except Exception as e:
        logging.critical(f"\n❌ Erro crítico: {str(e)}")
        if ENABLE_EMAIL_ALERTS:
            enviar_email_alerta(log_filename)

# FIM DO SCRIPT
