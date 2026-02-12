import oci
import csv
import logging
import sys

# Configuração de Logs para exibir progresso
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler(sys.stdout)
])

# Carrega configuração padrão do OCI (~/.oci/config)
config = oci.config.from_file()

# Inicializa clientes OCI para Identity
identity_client = oci.identity.IdentityClient(config)
tenancy_id = config['tenancy']

# --- Funções Auxiliares ---
def get_instance_os_info(compute_client, instance):
    """Obtém o nome e a versão do sistema operacional de uma instância."""
    try:
        image = compute_client.get_image(instance.image_id).data
        if image:
            return image.operating_system, image.operating_system_version
        return "Desconhecido", "Desconhecido"
    except Exception:
        return "Erro ao obter SO", "Erro ao obter Versão"

def get_instance_tags(instance):
    """Obtém as tags de forma livre e definidas da instância."""
    return {
        "Freeform Tags": instance.freeform_tags if instance.freeform_tags else {},
        "Defined Tags": instance.defined_tags if instance.defined_tags else {}
    }

def get_backup_policy_name(block_storage_client, volume_id):
    """Obtém a política de backup associada a um volume."""
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
    except Exception:
        return "Erro ao obter"

# --- Lógica Principal ---
def run_inventory_report():
    output = []
    
    # Lista todas as regiões inscritas na tenancy
    logging.info("Buscando regiões ativas...")
    regions = [r.region_name for r in identity_client.list_region_subscriptions(tenancy_id).data]
    logging.info(f"Regiões encontradas: {', '.join(regions)}")

    for region in regions:
        logging.info(f"\nIniciando coleta de dados na região: {region}")
        config['region'] = region

        # Inicializa clientes de serviço para a região atual
        compute_client = oci.core.ComputeClient(config)
        block_storage_client = oci.core.BlockstorageClient(config)
        network_client = oci.core.VirtualNetworkClient(config)

        # Lista todos os compartimentos (inclusive o root)
        try:
            compartments = oci.pagination.list_call_get_all_results(
                identity_client.list_compartments,
                tenancy_id,
                compartment_id_in_subtree=True
            ).data
            compartments.append(identity_client.get_compartment(tenancy_id).data)
        except Exception as e:
            logging.error(f"Erro ao listar compartimentos na região {region}: {e}")
            continue

        for compartment in compartments:
            logging.info(f"  Processando compartimento: {compartment.name}")
            try:
                instances = oci.pagination.list_call_get_all_results(
                    compute_client.list_instances,
                    compartment.id
                ).data
            except Exception as e:
                logging.error(f"  Erro ao listar instâncias no compartimento {compartment.name}: {e}")
                continue

            for instance in instances:
                logging.info(f"    Coletando dados para: {instance.display_name}")
                inst_data = {
                    "Region": region,
                    "Instance Name": instance.display_name,
                    "Compartment": compartment.name,
                    "OCID": instance.id,
                    "Availability Domain": instance.availability_domain,
                    "State": instance.lifecycle_state,
                    "Private IP": "",
                    "Public IP": "",
                    "OCPUs": "",
                    "Memory (GB)": "",
                    "Operating System": "",
                    "OS Version": "",
                    "Boot Volume Name": "",
                    "Boot Volume Size (GB)": "",
                    "Boot Volume Backup Policy": "",
                    "Block Volumes Names": "",
                    "Block Volumes Sizes (GB)": "",
                    "Block Volume Backup Policy": "",
                    "Freeform Tags": "",
                    "Defined Tags": ""
                }
                
                # Coleta de informações de forma e recursos
                try:
                    if instance.shape.startswith("VM.Standard") and instance.shape_config:
                        inst_data["OCPUs"] = instance.shape_config.ocpus
                        inst_data["Memory (GB)"] = instance.shape_config.memory_in_gbs
                except Exception:
                    pass

                # Coleta de IPs
                try:
                    vnics = oci.pagination.list_call_get_all_results(
                        compute_client.list_vnic_attachments,
                        compartment_id=compartment.id,
                        instance_id=instance.id
                    ).data
                    private_ips = []
                    public_ips = []
                    for vnic_attachment in vnics:
                        vnic = network_client.get_vnic(vnic_attachment.vnic_id).data
                        private_ips.append(vnic.private_ip)
                        public_ips.append(vnic.public_ip if vnic.public_ip else "None")
                    inst_data["Private IP"] = ", ".join(private_ips)
                    inst_data["Public IP"] = ", ".join(public_ips)
                except Exception:
                    inst_data["Private IP"] = "Erro ao obter"
                    inst_data["Public IP"] = "Erro ao obter"
                
                # Coleta de informações do SO
                os_name, os_version = get_instance_os_info(compute_client, instance)
                inst_data["Operating System"] = os_name
                inst_data["OS Version"] = os_version

                # Coleta de detalhes do Boot Volume
                try:
                    boot_attachments = oci.pagination.list_call_get_all_results(
                        compute_client.list_boot_volume_attachments,
                        availability_domain=instance.availability_domain,
                        compartment_id=compartment.id,
                        instance_id=instance.id
                    ).data
                    if boot_attachments:
                        boot_vol = block_storage_client.get_boot_volume(boot_attachments[0].boot_volume_id).data
                        inst_data["Boot Volume Name"] = boot_vol.display_name
                        inst_data["Boot Volume Size (GB)"] = boot_vol.size_in_gbs
                        inst_data["Boot Volume Backup Policy"] = get_backup_policy_name(block_storage_client, boot_vol.id)
                except Exception:
                    inst_data["Boot Volume Backup Policy"] = "Erro ao obter"
                
                # Coleta de detalhes dos Block Volumes
                try:
                    block_attachments = oci.pagination.list_call_get_all_results(
                        compute_client.list_volume_attachments,
                        compartment_id=compartment.id,
                        instance_id=instance.id
                    ).data
                    volumes = []
                    sizes = []
                    policies = []
                    for att in block_attachments:
                        vol = block_storage_client.get_volume(att.volume_id).data
                        volumes.append(vol.display_name)
                        sizes.append(str(vol.size_in_gbs))
                        policies.append(get_backup_policy_name(block_storage_client, vol.id))
                    inst_data["Block Volumes Names"] = ", ".join(volumes)
                    inst_data["Block Volumes Sizes (GB)"] = ", ".join(sizes)
                    inst_data["Block Volume Backup Policy"] = ", ".join(policies)
                except Exception:
                    inst_data["Block Volume Backup Policy"] = "Erro ao obter"

                # Coleta de Tags
                tags = get_instance_tags(instance)
                inst_data["Freeform Tags"] = str(tags["Freeform Tags"])
                inst_data["Defined Tags"] = str(tags["Defined Tags"])
                
                output.append(inst_data)

    # Exporta para CSV
    csv_file = "oci_inventory_full_report_multi_region.csv"
    if output:
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=output[0].keys())
            writer.writeheader()
            writer.writerows(output)
        logging.info(f"\n✅ Relatório gerado com sucesso: '{csv_file}'")
    else:
        logging.warning("⚠️ Nenhum dado foi coletado. Verifique as permissões do seu usuário.")

if __name__ == "__main__":
    run_inventory_report()