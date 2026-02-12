import oci
import csv

CSV_FILE = "instances_region_os.csv"

config = oci.config.from_file()
config['region'] = 'sa-saopaulo-1'  # Região definida

compute_client = oci.core.ComputeClient(config)
identity_client = oci.identity.IdentityClient(config)

tenancy_id = config['tenancy']

# Lista todos os compartimentos na tenancy
compartments = oci.pagination.list_call_get_all_results(
    identity_client.list_compartments,
    tenancy_id,
    compartment_id_in_subtree=True
).data
compartments.append(identity_client.get_compartment(tenancy_id).data)  # Adiciona o compartimento root

def get_instance_os_info(instance):
    try:
        image = compute_client.get_image(instance.image_id).data
        if image:
            return image.operating_system, image.operating_system_version
        return "Desconhecido", "Desconhecido"
    except:
        return "Erro ao obter SO", "Erro ao obter Versão"

def listar_instancias():
    output = []

    for compartment in compartments:
        try:
            instances = oci.pagination.list_call_get_all_results(
                compute_client.list_instances,
                compartment.id
            ).data
        except Exception as e:
            print(f"Erro ao listar instâncias no compartimento {compartment.name}: {e}")
            continue

        for instance in instances:
            os_name, os_version = get_instance_os_info(instance)

            output.append({
                "Instance Name": instance.display_name,
                "Compartment": compartment.name,
                "OCID": instance.id,
                "State": instance.lifecycle_state,
                "Operating System": os_name,
                "Version": os_version
            })
            
            print(f"✅ {instance.display_name} - SO: {os_name}, Versão: {os_version}")

    # Exporta para CSV
    if output:
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=output[0].keys())
            writer.writeheader()
            writer.writerows(output)

        print(f"\n📁 Exportado com sucesso para '{CSV_FILE}'")
    else:
        print("⚠️ Nenhum dado foi coletado. Verifique permissões ou filtros.")

if __name__ == "__main__":
    listar_instancias()
