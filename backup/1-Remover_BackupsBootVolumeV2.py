import oci
import time
import random
from datetime import datetime, timezone

# Adicionando o parâmetro para habilitar/desabilitar confirmação manual
CONFIRMAR_EXCLUSAO = False  # Altere para True se quiser que o script peça confirmação

COMPARTMENT_NAME = "LinuxBancoDados"
KEYWORD = "BKPAUTCITEL-"
RETENTION_COUNT = 5
LOG_FILE = 'exclusao_backups.log'

config = oci.config.from_file()
config['region'] = 'sa-saopaulo-1'

block_storage = oci.core.BlockstorageClient(config)
identity = oci.identity.IdentityClient(config)

def get_compartment_id():
    compartments = oci.pagination.list_call_get_all_results(
        identity.list_compartments,
        config['tenancy'],
        compartment_id_in_subtree=True
    ).data
    for comp in compartments:
        if comp.name == COMPARTMENT_NAME:
            return comp.id
    raise ValueError(f"Compartment {COMPARTMENT_NAME} não encontrado")

def list_backup_with_backoff(backup_id, backup_name, max_retentativas=5):
    espera = 5
    for tentativa in range(max_retentativas):
        try:
            print(f" 🚨 🚨 🚨️ Este Backup do Disco SERA EXCLUIDO: ⚠️ ⚠️ ⚠️ {backup_name} 🚨 🚨 🚨")
            block_storage.delete_boot_volume_backup(backup_id)
            return True
        except oci.exceptions.ServiceError as e:
            if e.status == 429 and "TooManyRequests" in str(e):
                print(f"⚠️ Tentativa {tentativa+1}: Limite de requisições (429). Aguardando {espera}s...")
                time.sleep(espera + random.uniform(0, 5))
                espera *= 2
            else:
                print(f"❌ Erro ao excluir {backup_name}: {str(e)}")
                return False
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
            return False
    return False

def get_boot_volume_name(volume_id):
    try:
        volume = block_storage.get_boot_volume(volume_id).data
        return volume.display_name
    except Exception as e:
        return f"Nome não encontrado (erro: {str(e)})"

def log_exclusion(volume_id, volume_name, backups):
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{datetime.now(timezone.utc)} - Volume {volume_id} ({volume_name})\n")
        for backup in backups:
            log_file.write(f"  Excluído: {backup.display_name} (OCID: {backup.id})\n")

def delete_old_boot_volume_backups():
    compartment_id = get_compartment_id()
    backups = oci.pagination.list_call_get_all_results(
        block_storage.list_boot_volume_backups,
        compartment_id=compartment_id
    ).data

    backups_filtered = [
        b for b in backups
        if KEYWORD in b.display_name and b.lifecycle_state == "AVAILABLE"
    ]

    backups_by_volume = {}
    for backup in backups_filtered:
        volume_id = backup.boot_volume_id
        backups_by_volume.setdefault(volume_id, []).append(backup)

    for volume_id, backups in backups_by_volume.items():
        backups_sorted = sorted(backups, key=lambda x: x.time_created, reverse=True)
        volume_name = get_boot_volume_name(volume_id)

        if len(backups_sorted) > RETENTION_COUNT:
            backups_to_delete = backups_sorted[RETENTION_COUNT:]
            backup_names = ", ".join([b.display_name for b in backups_to_delete])
            print(f"\n🚨 Volume {volume_id} ({volume_name}) tem mais de {RETENTION_COUNT} backups.")
            print(f"Os seguintes backups serão excluídos: {backup_names}")

            if not CONFIRMAR_EXCLUSAO or input("Deseja continuar com a exclusão? (s/N): ").lower() == 's':
                for backup in backups_to_delete:
                    if list_backup_with_backoff(backup.id, backup.display_name):
                        log_exclusion(volume_id, volume_name, backups_to_delete)
                    else:
                        print("❌ Exclusão cancelada pelo analista.")
            else:
                print("❌ Exclusão cancelada pelo analista.")
        else:
            backup_names = ", ".join([b.display_name for b in backups_sorted])
            print(f"⚠️ Volume {volume_id} ({volume_name}) tem apenas {len(backups_sorted)} backups ({backup_names}). Nenhum backup excluído.")
            print(" ❗ ❗ ❗️  Esses discos não têm a quantidade de retenção da política.  ❗ ❗ ❗️ ")

if __name__ == "__main__":
    delete_old_boot_volume_backups()
    print("\n✅ Execução concluída para boot volume backups")

