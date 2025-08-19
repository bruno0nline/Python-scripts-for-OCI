import oci
import csv
import logging
import os
import sys
from datetime import datetime

# --- Configurações ---
CSV_FILE = "oci_instances_backup_policies_report.csv"
LOG_DIR = "./logs"

# Lista de regiões a serem processadas
# Comente as regiões que você não deseja incluir no relatório
# Exemplo: regions_to_process = ['sa-saopaulo-1']
regions_to_process = [
    'sa-saopaulo-1',  # Região Brazil East
    'sa-vinhedo-1',   # Região Vinhedo
    # 'us-ashburn-1'  # Região Ashburn
]

# --- Configuração de Log ---
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
log_filename = os.path.join(LOG_DIR, f"report_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_filename),
    logging.StreamHandler(sys.stdout)
])

# --- Funções Auxiliares ---
def get_backup_policy_name(volume_id, block_storage_client):
    """
    Obtém a política de backup associada a um volume.
    """
    try:
        policies = oci.pagination.list_call_get_all_results(
            block_storage_client.get_volume_backup_policy_asset_assignment,
            asset_id=volume_id
        ).data

        if not policies:
            return "Nenhuma"

        policy_names = []
        for policy in policies:
            policy_details = block_storage_client.get_volume_backup_policy(policy.policy_id).data
            policy_names.append(policy_details.display_name)

        return ", ".join(policy_names)
    except Exception as e:
        return f"Erro ao obter política: {e}"

def get_instance_os_info(instance, compute_client):
    """
    Obtém o nome e a versão do sistema operacional de uma instância.
    """
    try:
        if instance.source_details.source_type == "image":
            image = compute_client.get_image(instance.source_details.image_id).data
            return image.operating_system, image.operating_system_version
        return "Desconhecido", "Desconhecido"
    except Exception as e:
        return "Erro ao obter SO", "Erro ao obter Versão"

def listar_instancias_e_politicas():
    """
    Lista todas as instâncias, seus volumes e políticas de backup associadas
    nas regiões especificadas e exporta para um arquivo CSV.
    """
    # Carrega a configuração padrão do OCI
    config = oci.config.from_file()
    identity_client = oci.identity.IdentityClient(config)
    tenancy_id = config['tenancy']
    
    # Lista todos os compartimentos (inclusive o root)
    logging.info("Listando compartimentos na tenancy...")
    try:
        compartments = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            tenancy_id,
            compartment_id_in_subtree=True
        ).data
        compartments.append(identity_client.get_compartment(tenancy_id).data)
    except Exception as e:
        logging.error(f"Erro ao listar compartimentos: {e}")
        return

    # Cabeçalho do CSV
    fieldnames = ["Region", "Compartment", "Instance Name", "Instance OCID", "Operating System", "Volume Type", "Volume Name", "Volume OCID", "Backup Policy"]
    
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        # Loop por região
        for region in regions_to_process:
            logging.info(f"\nIniciando processamento na região: {region}...")
            config['region'] = region
            try:
                compute_client = oci.core.ComputeClient(config)
                block_storage_client = oci.core.BlockstorageClient(config)
            except Exception as e:
                logging.error(f"Erro ao criar clientes OCI para a região {region}: {e}")
                continue

            # Loop por compartment
            for comp in compartments:
                if comp.lifecycle_state != "ACTIVE":
                    continue
                logging.info(f"  > Processando compartment: {comp.name}")
                
                try:
                    instances = oci.pagination.list_call_get_all_results(
                        compute_client.list_instances,
                        compartment_id=comp.id
                    ).data
                except Exception as e:
                    logging.warning(f"    - Erro ao listar instâncias no compartment {comp.name}: {e}")
                    continue
                
                # Loop por instância
                for instance in instances:
                    logging.info(f"    -> Instância: {instance.display_name}")
                    
                    os_name, os_version = get_instance_os_info(instance, compute_client)
                    
                    # Boot Volumes
                    try:
                        boot_attachments = compute_client.list_boot_volume_attachments(
                            availability_domain=instance.availability_domain,
                            compartment_id=comp.id,
                            instance_id=instance.id
                        ).data
                        for bva in boot_attachments:
                            boot_volume = block_storage_client.get_boot_volume(bva.boot_volume_id).data
                            policy_name = get_backup_policy_name(boot_volume.id, block_storage_client)
                            writer.writerow({
                                "Region": region,
                                "Compartment": comp.name,
                                "Instance Name": instance.display_name,
                                "Instance OCID": instance.id,
                                "Operating System": f"{os_name} {os_version}",
                                "Volume Type": "Boot Volume",
                                "Volume Name": boot_volume.display_name,
                                "Volume OCID": boot_volume.id,
                                "Backup Policy": policy_name
                            })
                    except Exception as e:
                        logging.warning(f"      - Erro ao processar Boot Volume da instância {instance.display_name}: {e}")

                    # Block Volumes
                    try:
                        block_attachments = compute_client.list_volume_attachments(
                            compartment_id=comp.id,
                            instance_id=instance.id
                        ).data
                        for va in block_attachments:
                            block_volume = block_storage_client.get_volume(va.volume_id).data
                            policy_name = get_backup_policy_name(block_volume.id, block_storage_client)
                            writer.writerow({
                                "Region": region,
                                "Compartment": comp.name,
                                "Instance Name": instance.display_name,
                                "Instance OCID": instance.id,
                                "Operating System": f"{os_name} {os_version}",
                                "Volume Type": "Block Volume",
                                "Volume Name": block_volume.display_name,
                                "Volume OCID": block_volume.id,
                                "Backup Policy": policy_name
                            })
                    except Exception as e:
                        logging.warning(f"      - Erro ao processar Block Volume da instância {instance.display_name}: {e}")

    logging.info(f"\n✅ Relatório concluído! Verifique o arquivo '{CSV_FILE}' para os resultados.")

if __name__ == "__main__":
    listar_instancias_e_politicas()