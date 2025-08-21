import oci
import json
import logging
import sys

# --- Padrões de Nomenclatura ---
# oci-<serviço>-<ação>
# Exemplo: oci-network-vcn-collector.py

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler(sys.stdout)
])

# --- Funções ---
def run_vcn_collector():
    """
    Coleta e exporta detalhes das VCNs em todos os compartimentos de todas as regiões.
    """
    try:
        # Carrega a configuração do arquivo padrão
        config = oci.config.from_file("~/.oci/config")
        identity_client = oci.identity.IdentityClient(config)
        
        tenancy_id = config["tenancy"]

        # Lista para armazenar os detalhes das VCNs
        all_vcn_details = []

        logging.info("Buscando todas as regiões ativas na tenancy...")
        regions = [r.region_name for r in identity_client.list_region_subscriptions(tenancy_id).data]
        logging.info(f"Regiões encontradas: {', '.join(regions)}")

        # Itera sobre cada região
        for region in regions:
            logging.info(f"\n--- Processando região: {region} ---")
            config['region'] = region

            # Inicializa os clientes da OCI para a região atual
            virtual_network_client = oci.core.VirtualNetworkClient(config)

            logging.info("Buscando todos os compartimentos na tenancy...")
            # Lista todos os compartimentos, incluindo sub-compartimentos
            compartments = oci.pagination.list_call_get_all_results(
                identity_client.list_compartments,
                tenancy_id,
                compartment_id_in_subtree=True
            ).data

            # Adiciona o compartimento raiz à lista
            compartments.append(identity_client.get_compartment(tenancy_id).data)

            # Itera sobre os compartimentos e busca as VCNs
            for compartment in compartments:
                if compartment.lifecycle_state == "ACTIVE":
                    logging.info(f"  Listando VCNs no compartimento: {compartment.name}")
                    
                    try:
                        vcn_response = oci.pagination.list_call_get_all_results(
                            virtual_network_client.list_vcns,
                            compartment_id=compartment.id
                        )
                        
                        for vcn in vcn_response.data:
                            logging.info(f"    VCN encontrada: {vcn.display_name}")
                            all_vcn_details.append({
                                "compartment": compartment.name,
                                "vcn_name": vcn.display_name,
                                "vcn_id": vcn.id,
                                "region": region
                            })
                    except oci.exceptions.ServiceError as e:
                        logging.error(f"  Erro ao listar VCNs no compartimento {compartment.name}: {e.message}")
                        continue
        
        # Exporta os detalhes das VCNs para um arquivo JSON
        output_file = "vcn_details_all_regions.json"
        with open(output_file, "w") as file:
            json.dump(all_vcn_details, file, indent=4)

        logging.info(f"\n✅ Detalhes das VCNs de todas as regiões exportados para '{output_file}'.")

    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    run_vcn_collector()