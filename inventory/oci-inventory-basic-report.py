import oci
import csv
import sys

# Carrega configuração do OCI
# Funciona tanto localmente (~/.oci/config) quanto no Cloud Shell (autenticação automática)
try:
    config = oci.config.from_file()
    print("✓ Usando configuração de ~/.oci/config")
except Exception as e:
    print(f"⚠ Arquivo de config não encontrado, tentando autenticação de instância...")
    try:
        # Tenta usar autenticação de instância (Cloud Shell)
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        config = {'region': oci.config.DEFAULT_LOCATION}
        print("✓ Usando autenticação de instância (Cloud Shell)")
    except Exception as e2:
        print(f"✗ Erro ao configurar autenticação: {e2}")
        print("\nPor favor, configure o OCI CLI ou execute no Cloud Shell")
        sys.exit(1)

# Você pode alterar a região aqui se necessário (descomente a linha desejada)
# config['region'] = 'sa-saopaulo-1'  # Região Brazil East (São Paulo)
# config['region'] = 'sa-vinhedo-1'  # Região Vinhedo
# config['region'] = 'us-ashburn-1'  # Região Ashburn

print(f"✓ Região: {config.get('region', 'padrão')}")

compute_client = oci.core.ComputeClient(config)
block_storage_client = oci.core.BlockstorageClient(config)
network_client = oci.core.VirtualNetworkClient(config)
identity_client = oci.identity.IdentityClient(config)

# Obtém tenancy ID
try:
    tenancy_id = config['tenancy']
except KeyError:
    # Se não tiver no config, obtém do identity
    tenancy_id = identity_client.get_user(identity_client.base_client.signer.api_key.split('/')[3]).data.compartment_id

print(f"✓ Tenancy ID: {tenancy_id[:20]}...")
print("\n🔍 Listando compartimentos...")

# Lista domínios de disponibilidade
domains = identity_client.list_availability_domains(tenancy_id).data

# Lista todos os compartimentos (inclusive o root)
compartments = oci.pagination.list_call_get_all_results(
    identity_client.list_compartments,
    tenancy_id,
    compartment_id_in_subtree=True
).data
compartments.append(identity_client.get_compartment(tenancy_id).data)

def get_backup_policy_name(volume_id):
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

output = []

# Para cada compartimento
for compartment in compartments:
    try:
        instances = oci.pagination.list_call_get_all_results(
            compute_client.list_instances,
            compartment.id
        ).data
        if instances:
            print(f"  ✓ {compartment.name}: {len(instances)} instância(s)")
    except Exception as e:
        print(f"  ✗ Erro ao listar instâncias no compartimento {compartment.name}: {e}")
        continue

    for instance in instances:
        print(f"    → Processando: {instance.display_name}")
        inst_data = {
            "Instance Name": instance.display_name,
            "Compartment": compartment.name,
            "Availability Domain": instance.availability_domain,
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
            "Version": ""
        }

        try:
            if instance.shape.startswith("VM.Standard") and instance.shape_config:
                inst_data["OCPUs"] = instance.shape_config.ocpus
                inst_data["Memory (GB)"] = instance.shape_config.memory_in_gbs
        except:
            pass

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

        try:
            if instance.source_details.source_type == "image":
                image = compute_client.get_image(instance.source_details.image_id).data
                inst_data["Operating System"] = image.operating_system
                inst_data["Version"] = image.operating_system_version
        except:
            inst_data["Operating System"] = "Indisponível"
            inst_data["Version"] = "Indisponível"

        output.append(inst_data)

print(f"\n📊 Total de instâncias encontradas: {len(output)}")
print("💾 Gerando arquivo CSV...")

# Exporta para CSV
if output:
    csv_filename = "oci_instances_full_report.csv"
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=output[0].keys())
        writer.writeheader()
        writer.writerows(output)

    print(f"✅ Exportado com sucesso para {csv_filename}")
    print(f"📄 Total de {len(output)} instância(s) no relatório")
else:
    print("⚠️ Nenhum dado foi coletado. Verifique permissões ou filtros.")
