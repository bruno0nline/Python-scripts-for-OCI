import oci
import csv

# Configuração OCI
config = oci.config.from_file()
config["region"] = "sa-saopaulo-1"  # Região Brazil East

block_client = oci.core.BlockstorageClient(config)
identity_client = oci.identity.IdentityClient(config)
tenancy_id = config["tenancy"]

# Lista todos os compartimentos (inclusive o root)
compartments = oci.pagination.list_call_get_all_results(
    identity_client.list_compartments,
    tenancy_id,
    compartment_id_in_subtree=True
).data
compartments.append(identity_client.get_compartment(tenancy_id).data)

# Pega domínios de disponibilidade
ads = identity_client.list_availability_domains(tenancy_id).data

volumes_output = []

for compartment in compartments:
    for ad in ads:
        # Boot Volumes
        boot_volumes = oci.pagination.list_call_get_all_results(
            block_client.list_boot_volumes,
            availability_domain=ad.name,
            compartment_id=compartment.id
        ).data

        for bv in boot_volumes:
            size = bv.size_in_gbs or 0
            vpu = bv.vpus_per_gb or 0
            iops = round(size * vpu * 75)
            throughput = round(size * vpu * 0.6, 2)

            volumes_output.append({
                "Compartimento": compartment.name,
                "Tipo": "Boot Volume",
                "Nome": bv.display_name,
                "Availability Domain": ad.name,
                "Tamanho (GB)": size,
                "vPU/GB": vpu,
                "IOPS (estimado)": iops,
                "Throughput (MB/s est.)": throughput
            })

        # Block Volumes
        block_volumes = oci.pagination.list_call_get_all_results(
            block_client.list_volumes,
            availability_domain=ad.name,
            compartment_id=compartment.id
        ).data

        for vol in block_volumes:
            size = vol.size_in_gbs or 0
            vpu = vol.vpus_per_gb or 0
            iops = round(size * vpu * 75)
            throughput = round(size * vpu * 0.6, 2)

            volumes_output.append({
                "Compartimento": compartment.name,
                "Tipo": "Block Volume",
                "Nome": vol.display_name,
                "Availability Domain": ad.name,
                "Tamanho (GB)": size,
                "vPU/GB": vpu,
                "IOPS (estimado)": iops,
                "Throughput (MB/s est.)": throughput
            })

# Exporta para CSV
if volumes_output:
    with open("oci_boot_and_block_volumes.csv", mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=volumes_output[0].keys())
        writer.writeheader()
        writer.writerows(volumes_output)

    print("✅ Exportado com sucesso para oci_boot_and_block_volumes.csv")
else:
    print("⚠️ Nenhum volume encontrado.")