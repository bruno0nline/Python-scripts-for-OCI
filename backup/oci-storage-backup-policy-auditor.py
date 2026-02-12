import oci
import csv
import logging
import sys
from collections import defaultdict

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler(sys.stdout)
])

# --- Funções ---
def get_instance_info_from_volume(compute_client, compartment_id, volume_id):
    """
    Retorna o nome e OCID da instância a qual um volume está anexado.
    Retorna None se o volume não estiver anexado.
    """
    try:
        attachments = oci.pagination.list_call_get_all_results(
            compute_client.list_volume_attachments,
            compartment_id=compartment_id,
            volume_id=volume_id
        ).data
        if attachments:
            instance_id = attachments[0].instance_id
            instance = compute_client.get_instance(instance_id).data
            return instance.display_name, instance.id
    except oci.exceptions.ServiceError as e:
        if e.code == "NotFound":
            return "Volume não anexado", None
        logging.warning(f"  Erro ao obter dados da instância para o volume {volume_id}: {e}")
    except Exception as e:
        logging.warning(f"  Erro ao obter dados da instância para o volume {volume_id}: {e}")
    return "Volume não anexado", None

def get_instance_info_from_boot_volume(compute_client, compartment_id, boot_volume_id):
    """
    Retorna o nome e OCID da instância a qual um volume de boot está anexado.
    Retorna None se o volume de boot não estiver anexado.
    """
    try:
        attachments = oci.pagination.list_call_get_all_results(
            compute_client.list_boot_volume_attachments,
            compartment_id=compartment_id,
            boot_volume_id=boot_volume_id
        ).data
        if attachments:
            instance_id = attachments[0].instance_id
            instance = compute_client.get_instance(instance_id).data
            return instance.display_name, instance.id
    except oci.exceptions.ServiceError as e:
        if e.code == "NotFound":
            return "Boot Volume não anexado", None
        logging.warning(f"  Erro ao obter dados da instância para o Boot Volume {boot_volume_id}: {e}")
    except Exception as e:
        logging.warning(f"  Erro ao obter dados da instância para o Boot Volume {boot_volume_id}: {e}")
    return "Boot Volume não anexado", None

def audit_backup_policies():
    """
    Audita todas as políticas de backup e lista os volumes e instâncias associados.
    O resultado é exportado para um arquivo CSV.
    """
    try:
        config = oci.config.from_file()
        identity_client = oci.identity.IdentityClient(config)
        block_storage_client = oci.core.BlockstorageClient(config)
        compute_client = oci.core.ComputeClient(config)
        
        tenancy_id = config["tenancy"]
        report_data = []

        logging.info("Buscando todos os compartimentos na tenancy...")
        compartments = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            tenancy_id,
            compartment_id_in_subtree=True
        ).data
        compartments.append(identity_client.get_compartment(tenancy_id).data)

        logging.info("Buscando todas as políticas de backup...")
        policies = oci.pagination.list_call_get_all_results(
            block_storage_client.list_volume_backup_policies,
            compartment_id=tenancy_id
        ).data

        for policy in policies:
            logging.info(f"Processando política: {policy.display_name}")
            
            # Buscar volumes de boot e blocos que usam esta política
            assets = oci.pagination.list_call_get_all_results(
                block_storage_client.get_volume_backup_policy_asset_assignment,
                policy_id=policy.id
            ).data

            if not assets:
                logging.info("  Nenhum volume encontrado para esta política.")
                continue

            for asset in assets:
                asset_id = asset.asset_id
                
                # Determinar o tipo de asset
                asset_type = asset_id.split('.')[1]
                
                compartment_id = policy.compartment_id
                compartment_name = "N/A"
                for comp in compartments:
                    if comp.id == compartment_id:
                        compartment_name = comp.name
                        break
                
                # Obter informações do volume e da instância
                if asset_type == "bootvolume":
                    try:
                        boot_volume = block_storage_client.get_boot_volume(asset_id).data
                        instance_name, instance_id = get_instance_info_from_boot_volume(compute_client, compartment_id, asset_id)
                        report_data.append({
                            "Backup Policy": policy.display_name,
                            "Compartment": compartment_name,
                            "Volume Name": boot_volume.display_name,
                            "Volume OCID": boot_volume.id,
                            "Volume Type": "Boot Volume",
                            "Instance Name": instance_name,
                            "Instance OCID": instance_id if instance_id else "N/A"
                        })
                    except oci.exceptions.ServiceError as e:
                        logging.warning(f"  Erro ao obter Boot Volume {asset_id}: {e}")
                
                elif asset_type == "volume":
                    try:
                        block_volume = block_storage_client.get_volume(asset_id).data
                        instance_name, instance_id = get_instance_info_from_volume(compute_client, compartment_id, asset_id)
                        report_data.append({
                            "Backup Policy": policy.display_name,
                            "Compartment": compartment_name,
                            "Volume Name": block_volume.display_name,
                            "Volume OCID": block_volume.id,
                            "Volume Type": "Block Volume",
                            "Instance Name": instance_name,
                            "Instance OCID": instance_id if instance_id else "N/A"
                        })
                    except oci.exceptions.ServiceError as e:
                        logging.warning(f"  Erro ao obter Block Volume {asset_id}: {e}")
        
        csv_file = "oci_backup_policy_auditor_report.csv"
        if report_data:
            with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=report_data[0].keys())
                writer.writeheader()
                writer.writerows(report_data)
            logging.info(f"\n✅ Relatório de auditoria de políticas de backup gerado com sucesso: '{csv_file}'")
        else:
            logging.warning("\n⚠️ Nenhum dado foi coletado. Verifique as permissões do seu usuário.")
            
    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    audit_backup_policies()