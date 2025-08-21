import oci
import csv

COMPARTMENT_NAME = "ClientesAutcom1"
CSV_FILE = "block_volumes.csv"

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

def get_backup_policy_name(volume_id):
    policies = oci.pagination.list_call_get_all_results(
        block_storage.get_volume_backup_policy_asset_assignment,
        asset_id=volume_id
    ).data

    if not policies:
        return "Nenhuma"

    policy_names = []
    for policy in policies:
        policy_details = block_storage.get_volume_backup_policy(policy.policy_id).data
        policy_names.append(policy_details.display_name)

    return ", ".join(policy_names)

def listar_block_volumes():
    compartment_id = get_compartment_id()
    block_volumes = oci.pagination.list_call_get_all_results(
        block_storage.list_volumes,
        compartment_id=compartment_id
    ).data

    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Nome", "OCID", "Backup Policy"])
        for bv in block_volumes:
            backup_policy_name = get_backup_policy_name(bv.id)
            writer.writerow([bv.display_name, bv.id, backup_policy_name])
            print(f"✅ {bv.display_name} exportado (Backup Policy: {backup_policy_name})")

if __name__ == "__main__":
    listar_block_volumes()
    print(f"\n📁 Arquivo '{CSV_FILE}' gerado com sucesso.")