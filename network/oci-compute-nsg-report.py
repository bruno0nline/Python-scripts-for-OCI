import oci
import csv
import logging
import sys

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler(sys.stdout)
])

# --- Funções ---
def get_instance_nsgs():
    """
    Lista todas as instâncias e extrai os NSGs associados às suas VNICs,
    analisando todas as regiões da tenancy. O resultado é exportado para um arquivo CSV.
    """
    try:
        config = oci.config.from_file()
        identity_client = oci.identity.IdentityClient(config)
        
        tenancy_id = config["tenancy"]
        report_data = []

        logging.info("Buscando todas as regiões ativas na tenancy...")
        regions = [r.region_name for r in identity_client.list_region_subscriptions(tenancy_id).data]
        logging.info(f"Regiões encontradas: {', '.join(regions)}")

        # Loop por cada região ativa
        for region in regions:
            logging.info(f"\n--- Processando região: {region} ---")
            config['region'] = region

            compute_client = oci.core.ComputeClient(config)
            network_client = oci.core.VirtualNetworkClient(config)

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
                    instances = oci.pagination.list_call_get_all_results(
                        compute_client.list_instances,
                        compartment_id=compartment.id
                    ).data
                except Exception as e:
                    logging.error(f"  Erro ao listar instâncias no compartimento {compartment.name}: {e}")
                    continue

                for instance in instances:
                    logging.info(f"    Verificando instância: {instance.display_name}")
                    
                    try:
                        vnic_attachments = oci.pagination.list_call_get_all_results(
                            compute_client.list_vnic_attachments,
                            compartment_id=compartment.id,
                            instance_id=instance.id
                        ).data
                        
                        nsg_names = []
                        for vnic_attachment in vnic_attachments:
                            vnic = network_client.get_vnic(vnic_attachment.vnic_id).data
                            
                            if vnic.nsg_ids:
                                for nsg_id in vnic.nsg_ids:
                                    nsg = network_client.get_network_security_group(nsg_id).data
                                    nsg_names.append(nsg.display_name)
                            
                        report_data.append({
                            "Region": region,
                            "Instance Name": instance.display_name,
                            "Compartment": compartment.name,
                            "Instance OCID": instance.id,
                            "Lifecycle State": instance.lifecycle_state,
                            "NSGs": ", ".join(nsg_names) if nsg_names else "Nenhum"
                        })
                    except Exception as e:
                        logging.error(f"    Erro ao obter NSGs para a instância {instance.display_name}: {e}")
                        report_data.append({
                            "Region": region,
                            "Instance Name": instance.display_name,
                            "Compartment": compartment.name,
                            "Instance OCID": instance.id,
                            "Lifecycle State": instance.lifecycle_state,
                            "NSGs": "Erro ao obter"
                        })

        csv_file = "oci_instance_nsg_report_all_regions.csv"
        if report_data:
            with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=report_data[0].keys())
                writer.writeheader()
                writer.writerows(report_data)
            logging.info(f"\n✅ Relatório de NSGs gerado com sucesso: '{csv_file}'")
        else:
            logging.warning("\n⚠️ Nenhum dado foi coletado. Verifique as permissões do seu usuário.")

    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    get_instance_nsgs()