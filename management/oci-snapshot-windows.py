import oci
import datetime
import csv
import os
import time

# Lista para armazenar os resultados.
results = []
# Define o nome do arquivo CSV de log.
csv_filename = f'snapshot_log_windows_only_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

# --- Início do script ---

# Configura o OCI usando a autenticação do Cloud Shell
try:
    config = oci.config.from_file('~/.oci/config', 'DEFAULT')
    identity_client = oci.identity.IdentityClient(config)
    compute_client = oci.core.ComputeClient(config)
    block_storage_client = oci.core.BlockstorageClient(config)
    tenancy_id = config['tenancy']
except Exception as e:
    print(f"Erro ao carregar a configuração da OCI. Verifique se o Cloud Shell está configurado corretamente. Erro: {e}")
    exit()

# Função para listar todos os compartimentos acessíveis
def get_all_compartment_ids(identity_client, tenancy_id):
    compartments = [tenancy_id]
    
    print("Buscando todos os compartimentos do tenant...")
    try:
        list_compartments_response = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE"
        )
        
        for c in list_compartments_response.data:
            if c.lifecycle_state == 'ACTIVE':
                compartments.append(c.id)
        
        print(f"Encontrados {len(compartments)} compartimentos ativos para busca.")
        return compartments
    except oci.exceptions.ServiceError as e:
        print(f"Erro ao tentar listar compartimentos. Verifique as permissões. Erro: {e}")
        print("Continuando a busca apenas no compartimento raiz.")
        return [tenancy_id]

all_compartment_ids = get_all_compartment_ids(identity_client, tenancy_id)
all_instances = []

# Varrer todos os compartimentos para encontrar as instâncias.
print("\nIniciando a varredura de todas as instâncias em todos os compartimentos...")
for compartment_id_to_check in all_compartment_ids:
    try:
        list_instances_response = compute_client.list_instances(
            compartment_id=compartment_id_to_check
        )
        for instance in list_instances_response.data:
            all_instances.append(instance)
    except oci.exceptions.ServiceError as e:
        print(f"Aviso: Pulando o compartimento {compartment_id_to_check}. Erro de permissão: {e.code}")
        
print(f"Total de instâncias encontradas: {len(all_instances)}\n")

for instance in all_instances:
    server_name = instance.display_name
    result_entry = {'ServerName': server_name, 'Status': 'Pulado', 'OS': 'Não Identificado', 'Message': 'Não é uma máquina Windows.'}
    print(f"--- Processando o servidor: {server_name} ---")

    try:
        # Pausa para evitar limites da API
        time.sleep(3)
        
        # Pega a imagem da instância para identificar o OS
        image = compute_client.get_image(image_id=instance.image_id).data
        detected_os = image.operating_system
        result_entry['OS'] = detected_os

        # Verifica se o OS é Windows (o nome é case-insensitive)
        if "windows" not in detected_os.lower():
            print(f"Aviso: Servidor '{server_name}' é um '{detected_os}', não é uma máquina Windows. Pulando o snapshot.")
        else:
            print(f"Identificado: Servidor '{server_name}' é um '{detected_os}'. Criando snapshot...")
            
            # --- Início da lógica de snapshot (mesmo código que funcionou para você) ---
            list_vbas_response = compute_client.list_boot_volume_attachments(
                availability_domain=instance.availability_domain,
                compartment_id=instance.compartment_id,
                instance_id=instance.id
            )

            boot_volume_attachments = list_vbas_response.data
            if not boot_volume_attachments:
                message = "Nenhum boot volume encontrado para a instância. Não foi possível criar o snapshot."
                print(f"Aviso: {message}")
                result_entry['Message'] = message
            else:
                boot_volume_id = boot_volume_attachments[0].boot_volume_id
                
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                snapshot_name = f'snap_BS4IT_{server_name}_patch_day_{current_date}'
                
                create_bv_backup_details = oci.core.models.CreateBootVolumeBackupDetails(
                    boot_volume_id=boot_volume_id,
                    display_name=snapshot_name,
                    type=oci.core.models.CreateBootVolumeBackupDetails.TYPE_FULL
                )
                
                create_bv_backup_response = block_storage_client.create_boot_volume_backup(
                    create_boot_volume_backup_details=create_bv_backup_details
                )
                
                message = f"Snapshot iniciado com sucesso. Estado inicial: {create_bv_backup_response.data.lifecycle_state}"
                print(f"Sucesso: {message}")
                result_entry['Status'] = 'Sucesso'
                result_entry['Message'] = message
            # --- Fim da lógica de snapshot ---

    except oci.exceptions.ServiceError as e:
        message = f"Ocorreu um erro na OCI ao processar o servidor. Erro: {e.code}"
        print(f"Erro: {message}")
        result_entry['Message'] = message
    except Exception as e:
        message = f"Ocorreu um erro inesperado: {e}"
        print(f"Erro: {message}")
        result_entry['Message'] = message
        
    results.append(result_entry)

# Escreve os resultados em um arquivo CSV.
try:
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['ServerName', 'OS', 'Status', 'Message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)
    print(f"\nArquivo de log '{csv_filename}' gerado com sucesso!")
except Exception as e:
    print(f"\nErro ao criar o arquivo CSV: {e}")

print("Processo de criação de snapshots concluído.")
print("Verifique o console da OCI para o status final dos snapshots.")
