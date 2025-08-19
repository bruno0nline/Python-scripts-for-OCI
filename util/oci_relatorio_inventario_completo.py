import oci
import csv
import json

# Carrega configuração padrão do OCI (~/.oci/config)
config = oci.config.from_file()
config['region'] = 'sa-saopaulo-1'  # Região Brazil East

# Clientes de serviço
compute_client = oci.core.ComputeClient(config)
block_storage_client = oci.core.BlockstorageClient(config)
network_client = oci.core.VirtualNetworkClient(config)
identity_client = oci.identity.IdentityClient(config)

tenancy_id = config['tenancy']

# Lista todos os compartimentos (inclusive o root)
compartments = oci.pagination.list_call_get_all_results(
    identity_client.list_compartments,
    tenancy_id,
    compartment_id_in_subtree=True
).data
compartments.append(identity_client.get_compartment(tenancy_id).data)

def get_backup_policy_name(volume_id):
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
        return f"Erro: {e}"

def get_instance_tags(instance):
    """
    Obtém as tags de forma livre e definidas da instância.
    """
    return {
        "Freeform Tags": instance.freeform_tags if instance.freeform_tags else {},
        "Defined Tags": instance.defined_tags if instance.defined_tags else {}
    }

def listar_instancias():
    """
    Lista todas as instâncias e exporta os dados completos para um arquivo CSV.
    """
    output = []

    # Para cada compartimento
    for compartment in compartments:
        try:
            instances = oci.pagination.list_call_get_all_results(
                compute_client.list_instances,
                compartment.id
            ).data
        except Exception as e:
            print(f"Erro ao listar instâncias no compartimento {compartment.name}: {e}")
            continue

        for instance in instances:
            inst_data = {
                "Instance Name": instance.display_name,
                "Compartment": compartment.name,
                "Availability Domain": instance.availability_domain,
                "State": instance.lifecycle_state,
                "OCID": instance.id,
                "Private IP": "",
                "Public IP": "",
                "OCPUs": "",
                "Memory (GB)": "",
                "Boot Volume": "",
                "Boot Volume Size (GB)": "",
                "Boot Volume Backup Policy": "",
                "Block Volumes": "",
                "Block Volumes Sizes (GB)": "",
                "Block Volume Backup Policy": "",
                "Operating System": "",
                "Version": "",
                "Freeform Tags": "",
                "Defined Tags": ""
            }

            # Obter informações de forma e recursos
            try:
                if instance.shape.startswith("VM.Standard") and instance.shape_config:
                    inst_data["OCPUs"] = instance.shape_config.ocpus
                    inst_data["Memory (GB)"] = instance.shape_config.memory_in_gbs
            except:
                pass

            # Obter informações de IP
            try:
                vnics = compute_client.list_vnic_attachments(
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
            except:
                inst_data["Private IP"] = "Erro ao obter"
                inst_data["Public IP"] = "Erro ao obter"

            # Obter informações do Boot Volume
            try:
                boot_attachments = compute_client.list_boot_volume_attachments(
                    availability_domain=instance.availability_domain,
                    compartment_id=compartment.id,
                    instance_id=instance.id
                ).data
                if boot_attachments:
                    boot_vol = block_storage_client.get_boot_volume(
                        boot_attachments[0].boot_volume_id).data
                    inst_data["Boot Volume"] = boot_vol.display_name
                    inst_data["Boot Volume Size (GB)"] = boot_vol.size_in_gbs
                    inst_data["Boot Volume Backup Policy"] = get_backup_policy_name(boot_vol.id)
            except:
                inst_data["Boot Volume Backup Policy"] = "Erro ao obter"

            # Obter informações dos Block Volumes
            try:
                block_attachments = compute_client.list_volume_attachments(
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
                    policies.append(get_backup_policy_name(vol.id))
                inst_data["Block Volumes"] = ", ".join(volumes)
                inst_data["Block Volumes Sizes (GB)"] = ", ".join(sizes)
                inst_data["Block Volume Backup Policy"] = ", ".join(policies)
            except:
                inst_data["Block Volume Backup Policy"] = "Erro ao obter"

            # Obter informações de Sistema Operacional
            try:
                if instance.source_details.source_type == "image":
                    image = compute_client.get_image(instance.source_details.image_id).data
                    inst_data["Operating System"] = image.operating_system
                    inst_data["Version"] = image.operating_system_version
            except:
                inst_data["Operating System"] = "Indisponível"
                inst_data["Version"] = "Indisponível"

            # Obter informações de Tags
            tags = get_instance_tags(instance)
            inst_data["Freeform Tags"] = json.dumps(tags["Freeform Tags"])
            inst_data["Defined Tags"] = json.dumps(tags["Defined Tags"])

            output.append(inst_data)

    # Exporta para CSV
    csv_file = "oci_instances_full_report_with_tags.csv"
    if output:
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            fieldnames = output[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output)
        print(f"✅ Exportado com sucesso para {csv_file}")
    else:
        print("⚠️ Nenhum dado foi coletado. Verifique permissões ou filtros.")

if __name__ == "__main__":
    listar_instancias()