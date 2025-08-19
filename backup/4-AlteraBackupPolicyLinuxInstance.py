#!/usr/bin/env python3
import oci
import subprocess
import json
import datetime
import logging
import os

# Configuração de logging
log_file = '/var/log/backup_policy_updater.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Nome do compartimento e da policy alvo
compartment_name = "ClientesAutcom1"
target_policy_name = "Bkp-Hora-Hora"

def get_compartment_ocid(identity_client, tenancy_id, compartment_name):
    try:
        compartments = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ANY"
        ).data

        for compartment in compartments:
            if compartment.name == compartment_name and compartment.lifecycle_state == "ACTIVE":
                return compartment.id
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar compartimento: {str(e)}")
        return None

def main():
    try:
        # Obter hora atual em UTC e calcular próxima hora
        now_utc = datetime.datetime.utcnow()
        target_hour = (now_utc.hour + 1) % 24
        
        logger.info(f"⏰ Hora atual UTC: {now_utc.hour:02d}:{now_utc.minute:02d}")
        logger.info(f"🎯 Definindo backup para próxima hora cheia: {target_hour:02d}:00 UTC")
        
        # Configuração OCI - Usando Instance Principal quando disponível
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            identity_client = oci.identity.IdentityClient(config, signer=signer)
            logger.info("Autenticação via Instance Principal")
        except Exception as auth_error:
            logger.warning(f"Falha Instance Principal: {str(auth_error)}")
            logger.warning("Usando autenticação por arquivo de configuração")
            config = oci.config.from_file()
            identity_client = oci.identity.IdentityClient(config)
        
        # Obter OCID do Tenancy
        tenancy_id = config["tenancy"] if "tenancy" in config else signer.tenancy_id
        
        # Obter OCID do compartimento
        compartment_ocid = get_compartment_ocid(identity_client, tenancy_id, compartment_name)
        
        if not compartment_ocid:
            logger.error(f"❌ ERRO: Compartimento '{compartment_name}' não encontrado ou inativo")
            return
        
        # Comando para listar policies
        cmd_list = [
            "oci", "bv", "volume-backup-policy", "list",
            "--compartment-id", compartment_ocid,
            "--output", "json"
        ]
        
        # Executar comando
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ ERRO na execução do OCI CLI: {result.stderr}")
            return
        
        try:
            policies = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error("❌ ERRO: Falha ao decodificar resposta JSON")
            return
        
        # Buscar e atualizar a policy
        policy_updated = False
        for policy in policies.get('data', []):
            if policy.get('display-name') == target_policy_name:
                logger.info("\n🔍 Policy encontrada:")
                logger.info(f"   Nome: {policy['display-name']}")
                logger.info(f"   OCID: {policy['id']}")
                
                # Preparar novo schedule
                new_schedules = []
                needs_update = False
                
                for schedule in policy.get('schedules', []):
                    current_hour = schedule.get('hour-of-day', -1)
                    
                    if current_hour != target_hour:
                        # Corrigir formato do horário (0-23)
                        new_hour = target_hour if target_hour < 24 else 0
                        logger.info(f"   ���️  Horário atual: {current_hour:02d}:00 | Novo horário: {new_hour:02d}:00")
                        schedule['hour-of-day'] = new_hour
                        needs_update = True
                    else:
                        logger.info(f"   ✅ Horário já configurado: {target_hour:02d}:00 (sem alteração necessária)")
                    
                    new_schedules.append(schedule)
                
                if not needs_update:
                    logger.info("ℹ️  Nenhuma atualização necessária")
                    policy_updated = True
                    continue
                
                # Atualizar a policy
                cmd_update = [
                    "oci", "bv", "volume-backup-policy", "update",
                    "--policy-id", policy['id'],
                    "--schedules", json.dumps(new_schedules),
                    "--force"
                ]
                
                # Executar com debug
                logger.info(f"Executando: {' '.join(cmd_update)}")
                update_result = subprocess.run(cmd_update, capture_output=True, text=True)
                
                if update_result.returncode == 0:
                    logger.info("\n✅ POLÍTICA ATUALIZADA COM SUCESSO!")
                    logger.info(f"   Novo horário de backup: {new_hour:02d}:00 UTC")
                    policy_updated = True
                else:
                    logger.error(f"\n❌ FALHA NA ATUALIZAÇÃO: {update_result.stderr}")
                    # Log adicional para diagnóstico
                    logger.debug(f"Comando completo: {' '.join(cmd_update)}")
                    logger.debug(f"Stdout: {update_result.stdout}")
        
        if not policy_updated:
            logger.error(f"\n❌ Policy '{target_policy_name}' não encontrada ou não atualizada")
    
    except Exception as e:
        logger.exception("Erro inesperado durante a execução")

if __name__ == "__main__":
    main()