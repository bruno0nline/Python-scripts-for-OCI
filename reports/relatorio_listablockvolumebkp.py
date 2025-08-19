import oci
import csv
 
COMPARTMENT_NAME = "LinuxBancoDados"
CSV_FILE = "block_volume_backups_filtrados.csv"
 
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
 
def listar_backups_filtrados():
    compartment_id = get_compartment_id()
    backups = oci.pagination.list_call_get_all_results(
        block_storage.list_volume_backups,
        compartment_id=compartment_id
    ).data
 
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Nome", "OCID"])
        for backup in backups:
            if "BKPAUTCITEL" in backup.display_name:
                writer.writerow([backup.display_name, backup.id])
                print(f"✅ {backup.display_name} exportado")
 
if __name__ == "__main__":
    listar_backups_filtrados()
    print(f"\n📁 Arquivo '{CSV_FILE}' gerado com sucesso.")