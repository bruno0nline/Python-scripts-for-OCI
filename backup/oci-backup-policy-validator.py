import oci
import csv
import logging
import os
import argparse
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# Códigos ANSI para cores
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
ORANGE = "\033[38;5;208m"

# Configurações padrão
DEFAULT_MIN_BACKUPS = 3
DEFAULT_MAX_AGE_HOURS = 1.5
DEFAULT_BACKUP_INTERVAL_HOURS = 1
COMPARTMENT_NAME = "LinuxBancoDados"

# Argumentos de linha de comando
parser = argparse.ArgumentParser(
    description="Valifica backups de volumes na Oracle Cloud.",
    epilog="Exemplo de uso:\n  python seu_script.py --min-backups 3 --max-age-hours 2 --backup-interval-hours 1 --limit 10 --source-type MANUAL --type FULL --lifecycle-state AVAILABLE",
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument("--min-backups", type=int, help="Número mínimo de backups esperados.")
parser.add_argument("--max-age-hours", type=int, help="Tempo máximo (em horas) desde o último backup.")
parser.add_argument("--backup-interval-hours", type=int, help="Intervalo esperado entre os backups (em horas).")
parser.add_argument("--limit", type=int, help="Limite de instâncias a serem analisadas. Para analisar todas, omita ou defina como 0 ou negativo.")
parser.add_argument("--source-type", type=str, help="Filtra backups por origem (ex: MANUAL, SCHEDULED).")
parser.add_argument("--type", type=str, help="Filtra backups por tipo (ex: INCREMENTAL, FULL).")
parser.add_argument("--lifecycle-state", type=str, help="Filtra backups por estado do ciclo de vida (ex: AVAILABLE, TERMINATED).")
args = parser.parse_args()

MIN_BACKUPS = args.min_backups if args.min_backups is not None else DEFAULT_MIN_BACKUPS
MAX_AGE_HOURS = args.max_age_hours if args.max_age_hours is not None else DEFAULT_MAX_AGE_HOURS
BACKUP_INTERVAL_HOURS = args.backup_interval_hours if args.backup_interval_hours is not None else DEFAULT_BACKUP_INTERVAL_HOURS
LIMIT = args.limit if args.limit is not None else 0
SOURCE_TYPE = args.source_type
TYPE = args.type
LIFECYCLE_STATE = args.lifecycle_state

# Diretório de logs
LOG_DIR = "./logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_filename = os.path.join(LOG_DIR, f"backup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_filename),
    logging.StreamHandler()
])

# Carrega configuração da OCI
config = oci.config.from_file()
config['region'] = 'sa-saopaulo-1'

# Inicializa os clients
compute_client = oci.core.ComputeClient(config)
block_storage_client = oci.core.BlockstorageClient(config)
identity_client = oci.identity.IdentityClient(config)

# Armazena os resumos por instância
resumo_por_instancia = defaultdict(list)

def get_compartment_id():
    compartments = oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        config['tenancy'],
        compartment_id_in_subtree=True
    ).data
    for comp in compartments:
        if comp.name == COMPARTMENT_NAME:
            return comp.id
    raise ValueError(f"Compartment {COMPARTMENT_NAME} não encontrado")

def verificar_backups(backups, volume_name, volume_type):
    now = datetime.now(timezone.utc)
    backups_sorted = sorted(backups, key=lambda b: b.time_created, reverse=True)
    recent_backups = backups_sorted[:MIN_BACKUPS]

    if len(recent_backups) < MIN_BACKUPS:
        logging.warning(f"⚠️ ALERTA: {volume_type} '{volume_name}' possui apenas {len(recent_backups)} backups.")
        return False

    for i, b in enumerate(recent_backups):
        max_allowed_age = timedelta(hours=MAX_AGE_HOURS + i * BACKUP_INTERVAL_HOURS)
        age = now - b.time_created
        if age > max_allowed_age:
            logging.warning(
                f"⚠️ ALERTA: {volume_type} '{volume_name}' - Backup '{b.display_name}' criado há {age} excede o limite de {max_allowed_age}."
            )
            return False

    logging.info(f"✅ {volume_type} '{volume_name}' possui {MIN_BACKUPS} backups dentro dos limites de tempo esperados.")
    return True

def exibir_backups(volume_backups, volume_name, volume_type):
    now = datetime.now(timezone.utc)
    print(f"    Total de backups encontrados: {len(volume_backups)}")
    logging.info(f"    Total de backups encontrados: {len(volume_backups)}")

    for b in sorted(volume_backups, key=lambda b: b.time_created, reverse=True):
        age = now - b.time_created
        status = "OK" if age <= timedelta(hours=MAX_AGE_HOURS) else "ALERTA"
        print(f"      - Backup: {b.display_name} | Tipo: {b.type} | Origem: {b.source_type} | Estado: {b.lifecycle_state} | Criado em: {b.time_created} | Status: {status}")
        logging.info(f"      - Backup: {b.display_name} | Tipo: {b.type} | Origem: {b.source_type} | Estado: {b.lifecycle_state} | Criado em: {b.time_created} | Status: {status}")

def processar_instancia(instancia, compartment_id):
    logging.info(f"\n{ORANGE}🖥️  Instância:{RESET} {BOLD}{ORANGE} {instancia.display_name}{RESET} - ID: {instancia.id}")
    print(f"\n{ORANGE}🖥️  Instância:{RESET} {BOLD}{ORANGE} {instancia.display_name}{RESET} - ID: {instancia.id}")

    instancias_com_backup = False

    # Boot Volumes
    boot_volume_attachments = oci.pagination.list_call_get_all_results(
        compute_client.list_boot_volume_attachments,
        availability_domain=instancia.availability_domain,
        compartment_id=compartment_id,
        instance_id=instancia.id
    ).data
    for bva in boot_volume_attachments:
        boot_volume = block_storage_client.get_boot_volume(bva.boot_volume_id).data
        print(f"  {BOLD}{GREEN}🟢 BootVolume:{RESET} {boot_volume.display_name} - ID: {boot_volume.id}")
        logging.info(f"  🟢 BootVolume: {boot_volume.display_name} - ID: {boot_volume.id}")

        backups = oci.pagination.list_call_get_all_results(
            block_storage_client.list_boot_volume_backups,
            compartment_id=compartment_id,
            boot_volume_id=boot_volume.id
        ).data

        # Aplicar filtros
        if SOURCE_TYPE:
            backups = [b for b in backups if b.source_type == SOURCE_TYPE]
        if TYPE:
            backups = [b for b in backups if b.type == TYPE]
        if LIFECYCLE_STATE:
            backups = [b for b in backups if b.lifecycle_state == LIFECYCLE_STATE]

        exibir_backups(backups, boot_volume.display_name, "BootVolume")
        status = "OK" if verificar_backups(backups, boot_volume.display_name, "BootVolume") else ("ALERTA" if backups else "SEM BACKUP")
        manual = sum(1 for b in backups if b.source_type == "MANUAL")
        scheduled = sum(1 for b in backups if b.source_type == "SCHEDULED")
        resumo_por_instancia[instancia.display_name].append(("BootVolume", boot_volume.display_name, status, len(backups), manual, scheduled))
        instancias_com_backup = instancias_com_backup or bool(backups)

    # Block Volumes
    volume_attachments = oci.pagination.list_call_get_all_results(
        compute_client.list_volume_attachments,
        compartment_id=compartment_id,
        instance_id=instancia.id
    ).data
    for va in volume_attachments:
        block_volume = block_storage_client.get_volume(va.volume_id).data
        print(f"  {BOLD}{BLUE}🔵 BlockVolume:{RESET} {block_volume.display_name} - ID: {block_volume.id}")
        logging.info(f"  🔵 BlockVolume: {block_volume.display_name} - ID: {block_volume.id}")

        backups = oci.pagination.list_call_get_all_results(
            block_storage_client.list_volume_backups,
            compartment_id=compartment_id,
            volume_id=block_volume.id
        ).data

        # Aplicar filtros
        if SOURCE_TYPE:
            backups = [b for b in backups if b.source_type == SOURCE_TYPE]
        if TYPE:
            backups = [b for b in backups if b.type == TYPE]
        if LIFECYCLE_STATE:
            backups = [b for b in backups if b.lifecycle_state == LIFECYCLE_STATE]

        exibir_backups(backups, block_volume.display_name, "BlockVolume")
        status = "OK" if verificar_backups(backups, block_volume.display_name, "BlockVolume") else ("ALERTA" if backups else "SEM BACKUP")
        manual = sum(1 for b in backups if b.source_type == "MANUAL")
        scheduled = sum(1 for b in backups if b.source_type == "SCHEDULED")
        resumo_por_instancia[instancia.display_name].append(("BlockVolume", block_volume.display_name, status, len(backups), manual, scheduled))
        instancias_com_backup = instancias_com_backup or bool(backups)

    return instancias_com_backup

def listar_instancias_e_volumes(compartment_id):
    instancias = oci.pagination.list_call_get_all_results(
        compute_client.list_instances,
        compartment_id=compartment_id
    ).data

    if LIMIT > 0:
        instancias = instancias[:LIMIT]

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(lambda instancia: processar_instancia(instancia, compartment_id), instancias)

def resumo_visual_por_instancia():
    print(f"\n{BOLD}{CYAN}📋 Resumo Visual por Instância e Volume:{RESET}")
    for inst, volumes in resumo_por_instancia.items():
        boot_volumes_count = sum(1 for v in volumes if v[0] == "BootVolume")
        block_volumes_count = sum(1 for v in volumes if v[0] == "BlockVolume")
        print(f"\n{BOLD}Instância:{RESET} {ORANGE}{inst}{RESET} | BootVolumes: {boot_volumes_count} | BlockVolumes: {block_volumes_count}")
        for tipo, nome, status, total, manual, scheduled in volumes:
            icone = "🟢" if status == "OK" else "🟡" if status == "ALERTA" else "🔴"
            print(f"  {icone} {tipo}: {nome} | Status: {status} | Backups: {total} (MANUAL: {manual}, SCHEDULED: {scheduled})")

def main():
    compartment_id = get_compartment_id()
    listar_instancias_e_volumes(compartment_id)
    resumo_visual_por_instancia()

if __name__ == "__main__":
    main()


