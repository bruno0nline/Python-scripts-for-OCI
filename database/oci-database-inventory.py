import oci
import csv
import logging
import sys

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler(sys.stdout)
])

# --- Funções ---
def run_database_inventory():
    """
    Coleta e exporta um inventário completo de DB Systems e Autonomous Databases
    de todas as regiões e compartimentos da tenancy.
    """
    try:
        config = oci.config.from_file()
        identity_client = oci.identity.IdentityClient(config)
        
        tenancy_id = config["tenancy"]
        report_data = []

        logging.info("Buscando todas as regiões ativas na tenancy...")
        regions = [r.region_name for r in identity_client.list_region_subscriptions(tenancy_id).data]
        logging.info(f"Regiões encontradas: {', '.join(regions)}")

        for region in regions:
            logging.info(f"\n--- Processando região: {region} ---")
            config['region'] = region

            database_client = oci.database.DatabaseClient(config)
            
            logging.info(f"Buscando todos os compartimentos na região {region}...")
            compartments = oci.pagination.list_call_get_all_results(
                identity_client.list_compartments,
                tenancy_id,
                compartment_id_in_subtree=True
            ).data
            compartments.append(identity_client.get_compartment(tenancy_id).data)

            for compartment in compartments:
                if compartment.lifecycle_state != "ACTIVE":
                    continue
                
                logging.info(f"  Processando compartimento: {compartment.name}")
                
                try:
                    # Coleta de DB Systems
                    db_systems = oci.pagination.list_call_get_all_results(
                        database_client.list_db_systems,
                        compartment_id=compartment.id
                    ).data
                    for db_system in db_systems:
                        report_data.append({
                            "Region": region,
                            "Compartment": compartment.name,
                            "Resource Type": "DB System",
                            "Name": db_system.display_name,
                            "OCID": db_system.id,
                            "Shape": db_system.shape,
                            "Version": db_system.version,
                            "Storage Size (GB)": db_system.data_storage_size_in_gbs,
                            "Lifecycle State": db_system.lifecycle_state,
                            "CPU Core Count": db_system.cpu_core_count
                        })

                    # Coleta de Autonomous Databases
                    autonomous_dbs = oci.pagination.list_call_get_all_results(
                        database_client.list_autonomous_databases,
                        compartment_id=compartment.id
                    ).data
                    for adb in autonomous_dbs:
                        report_data.append({
                            "Region": region,
                            "Compartment": compartment.name,
                            "Resource Type": "Autonomous Database",
                            "Name": adb.display_name,
                            "OCID": adb.id,
                            "Shape": adb.db_workload,
                            "Version": adb.db_version,
                            "Storage Size (GB)": adb.data_storage_size_in_gbs,
                            "Lifecycle State": adb.lifecycle_state,
                            "CPU Core Count": adb.cpu_core_count
                        })

                except Exception as e:
                    logging.error(f"  Erro ao listar databases no compartimento {compartment.name}: {e}")
                    continue

        # Exporta para CSV
        csv_file = "oci_database_inventory.csv"
        if report_data:
            with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
                fieldnames = report_data[0].keys()
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(report_data)
            logging.info(f"\n✅ Relatório de inventário de databases gerado com sucesso: '{csv_file}'")
        else:
            logging.warning("\n⚠️ Nenhum dado foi coletado. Verifique as permissões do seu usuário.")

    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    run_database_inventory()