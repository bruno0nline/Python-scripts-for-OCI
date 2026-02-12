import oci
import csv
import logging
from datetime import datetime
import os

# Configurações de saída
LOG_DIR = "./logs"
CSV_FILE = "oci_instances_volumes_all_regions.csv"

# Cria diretório de logs
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_filename = os.path.join(LOG_DIR, f"oci_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_filename),
    logging.StreamHandler()
])

# Carrega configuração OCI
config = oci.config.from_file()
identity_client = oci.identity.IdentityClient(config)

# Lista todas as regiões ativas
regions = [r.region_name for r in identity_client.list_region_subscriptions(config['tenancy']).data]

# Lista todos os compartments (inclusive sub-compartments)
compartments = oci.pagination.list_call_get_all_results(
    identity_client.list_compartments,
    config['tenancy'],
    compartment_id_in_subtree=True
).data

with open(CSV_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Region", "Compartment", "Instance Name", "Instance ID", "Volume Type", 
                     "Volume Name", "Volume ID", "Backup Name", "Source Type", "Created At"])

    # Loop por região
    for region in regions:
        logging.info(f"Processando região: {region}")
        config["region"] = region
        compute_client = oci.core.ComputeClient(config)
        block_storage_client = oci.core.BlockstorageClient(config)

        # Loop por compartment
        for comp in compartments:
            if comp.lifecycle_state != "ACTIVE":
                continue
            logging.info(f"  Compartment: {comp.name} ({comp.id})")

            try:
                instancias = oci.pagination.list_call_get_all_results(
                    compute_client.list_instances,
                    compartment_id=comp.id
                ).data
            except Exception as e:
                logging.error(f"Erro ao listar instâncias no compartment {comp.name}: {e}")
                continue

            for instancia in instancias:
                # Boot Volumes
                boot_attachments = oci.pagination.list_call_get_all_results(
                    compute_client.list_boot_volume_attachments,
                    availability_domain=instancia.availability_domain,
                    compartment_id=comp.id,
                    instance_id=instancia.id
                ).data
                for bva in boot_attachments:
                    boot_volume = block_storage_client.get_boot_volume(bva.boot_volume_id).data
                    backups = oci.pagination.list_call_get_all_results(
                        block_storage_client.list_boot_volume_backups,
                        compartment_id=comp.id,
                        boot_volume_id=boot_volume.id
                    ).data
                    for bvb in backups:
                        writer.writerow([region, comp.name, instancia.display_name, instancia.id,
                                         "BootVolume", boot_volume.display_name, boot_volume.id,
                                         bvb.display_name, bvb.source_type, bvb.time_created])

                # Block Volumes
                attachments = oci.pagination.list_call_get_all_results(
                    compute_client.list_volume_attachments,
                    compartment_id=comp.id,
                    instance_id=instancia.id
                ).data
                for va in attachments:
                    block_volume = block_storage_client.get_volume(va.volume_id).data
                    backups = oci.pagination.list_call_get_all_results(
                        block_storage_client.list_volume_backups,
                        compartment_id=comp.id,
                        volume_id=block_volume.id
                    ).data
                    for bvb in backups:
                        writer.writerow([region, comp.name, instancia.display_name, instancia.id,
                                         "BlockVolume", block_volume.display_name, block_volume.id,
                                         bvb.display_name, bvb.source_type, bvb.time_created])

logging.info(f"✅ Relatório gerado: {CSV_FILE}")
