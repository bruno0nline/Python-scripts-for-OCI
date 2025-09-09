import oci
import csv
import logging
import sys

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler(sys.stdout)
])

# --- Funções ---
def get_backup_policy_name(block_storage_client, volume_id):
    """Obtém a política de backup associada a um volume, se houver."""
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
        return f"Erro ao obter: {e}"

def get_instance_backup_policies():
    """
    Lista todas as instâncias e extrai as políticas de backup de seus volumes.
    O resultado é exportado para um arquivo CSV.
    """
    try:
        config = oci.config.from_file()
        identity_client = oci.identity.IdentityClient(config)
        compute_client = oci.core.ComputeClient(config)
        block_storage_client = oci.core.BlockstorageClient(config)
        
        tenancy_id = config["tenancy"]
        report_data = []

        logging.info("Buscando todos os compartimentos na tenancy...")
        compartments = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            tenancy_id,
            compartment_id_in_subtree=True
        ).data
        compartments.append(identity_client.get_compartment(tenancy_id).data)

        for compartment in compartments:
            if compartment.lifecycle_state != "ACTIVE":
                continue
            
            logging.info(f"Processando compartimento: {compartment.name}")
            
            try:
                instances = oci.pagination.list_call_get_all_results(
                    compute_client.list_instances,
                    compartment_id=compartment.id
                ).data
            except Exception as e:
                logging.error(f"  Erro ao listar instâncias no compartimento {compartment.name}: {e}")
                continue

            for instance in instances:
                logging.info(f"  Verificando políticas de backup para a instância: {instance.display_name}")

                boot_policy = "Nenhuma"
                block_policies = []

                # Coletando a política do Boot Volume
                try:
                    boot_attachments = oci.pagination.list_call_get_all_results(
                        compute_client.list_boot_volume_attachments,
                        availability_domain=instance.availability_domain,
                        compartment_id=compartment.id,
                        instance_id=instance.id
                    ).data
                    if boot_attachments:
                        boot_policy = get_backup_policy_name(block_storage_client, boot_attachments[0].boot_volume_id)
                except Exception as e:
                    logging.warning(f"    Erro ao obter política do Boot Volume para {instance.display_name}: {e}")
                
                # Coletando as políticas dos Block Volumes
                try:
                    block_attachments = oci.pagination.list_call_get_all_results(
                        compute_client.list_volume_attachments,
                        compartment_id=compartment.id,
                        instance_id=instance.id
                    ).data
                    if block_attachments:
                        for attachment in block_attachments:
                            block_policies.append(get_backup_policy_name(block_storage_client, attachment.volume_id))
                except Exception as e:
                    logging.warning(f"    Erro ao obter políticas dos Block Volumes para {instance.display_name}: {e}")

                report_data.append({
                    "Instance Name": instance.display_name,
                    "Compartment": compartment.name,
                    "Instance OCID": instance.id,
                    "Lifecycle State": instance.lifecycle_state,
                    "Boot Volume Backup Policy": boot_policy,
                    "Block Volumes Backup Policies": ", ".join(block_policies) if block_policies else "Nenhuma"
                })
                
        csv_file = "oci_instance_backup_policies.csv"
        if report_data:
            with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=report_data[0].keys())
                writer.writeheader()
                writer.writerows(report_data)
            logging.info(f"\n✅ Relatório de políticas de backup gerado com sucesso: '{csv_file}'")
        else:
            logging.warning("\n⚠️ Nenhum dado foi coletado. Verifique as permissões do seu usuário.")

    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    get_instance_backup_policies()