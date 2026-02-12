import oci
import csv
import time
import random
from oci.config import from_file

# OCIDs fornecidos
COMPARTMENT_VOLUMES_OCID = "ocid1.compartment.oc1..aaaaaaaa7pg2wt36j2cxsu72bbmhj5achprohkq2mxxnj4f4fearnvzomw6q"
BACKUP_POLICY_OCID = "ocid1.volumebackuppolicy.oc1.sa-saopaulo-1.amaaaaaalrh642iam4dnyutln7lc5fniiwvryfms5ke77jyi4axocpkobcwa"

# Configuração do OCI
config = from_file()
config['region'] = 'sa-saopaulo-1'  # Região específica

# Cliente OCI
block_storage_client = oci.core.BlockstorageClient(config)

def assign_backup_policy(volume_id, policy_id, max_retries=10):
    """Atribui a política de backup ao volume com tratamento robusto de erros 429"""
    espera = 5  # Tempo inicial de espera em segundos
    tentativa = 0

    while tentativa < max_retries:
        try:
            request_details = oci.core.models.VolumeBackupPolicyAssignment(
                policy_id=policy_id,
                asset_id=volume_id
            )
            block_storage_client.create_volume_backup_policy_assignment(request_details)
            print(f"✅ Volume {volume_id[:30]}... associado à política")
            return True
        
        except oci.exceptions.ServiceError as e:
            if e.status == 429 and "TooManyRequests" in str(e):
                print(f"⚠️ Tentativa {tentativa+1}: Limite de requisições (429). Aguardando {espera}s...")
                time.sleep(espera + random.uniform(0, 5))  # Adiciona variação aleatória
                espera *= 2  # Backoff exponencial
                tentativa += 1
            elif e.status == 400 and "PolicyAssignmentAlreadyExists" in str(e):
                print(f"ℹ️ Política já associada ao volume")
                return True
            else:
                print(f"❌ Erro [{e.status}]: {e.message}")
                return False
        
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
            return False
    
    print(f"⚠️ Falha após {max_retries} tentativas")
    return False

def list_volumes_with_retry(compartment_id, max_retries=5):
    """Lista volumes com tratamento de erros 429"""
    volumes = []
    next_page = None
    espera = 5
    tentativa = 0
    
    while tentativa < max_retries:
        try:
            print(f"🔍 Buscando volumes (tentativa {tentativa+1})...")
            while True:
                response = block_storage_client.list_volumes(
                    compartment_id=compartment_id,
                    page=next_page
                )
                volumes.extend(response.data)
                next_page = response.headers.get('opc-next-page')
                if not next_page:
                    return volumes
            break  # Sai do loop while se bem sucedido
            
        except oci.exceptions.ServiceError as e:
            if e.status == 429 and "TooManyRequests" in str(e):
                print(f"⚠️ Listagem: Limite de requisições (429). Aguardando {espera}s...")
                time.sleep(espera + random.uniform(0, 3))
                espera *= 2
                tentativa += 1
            else:
                print(f"❌ Erro na listagem: [{e.status}] {e.message}")
                raise
        except Exception as e:
            print(f"❌ Erro inesperado na listagem: {str(e)}")
            raise
    
    raise Exception(f"Falha após {max_retries} tentativas de listar volumes")

def main():
    try:
        # Lista todos os block volumes no compartment com tratamento de erro
        print(f"\n🔍 Iniciando busca de volumes no compartment:")
        print(f"   OCID: {COMPARTMENT_VOLUMES_OCID}")
        volumes = list_volumes_with_retry(COMPARTMENT_VOLUMES_OCID)
        print(f"📌 Total de volumes encontrados: {len(volumes)}")

        # Processa cada volume
        print("\n🚀 Iniciando associação de volumes à política de backup...")
        print(f"   Política OCID: {BACKUP_POLICY_OCID}")
        output = []
        success_count = 0
        skipped_count = 0
        failed_count = 0
        
        for i, volume in enumerate(volumes, 1):
            vol_id = volume.id
            vol_name = volume.display_name or "Sem nome"
            print(f"\n🔧 [{i}/{len(volumes)}] Processando: {vol_name}")
            print(f"   OCID: {vol_id[:50]}...")
            print(f"   Estado: {volume.lifecycle_state}, Tamanho: {volume.size_in_gbs} GB")
            
            if volume.lifecycle_state != "AVAILABLE":
                print("   ⚠️ Ignorado (volume não disponível)")
                status = "Ignorado - Estado inválido"
                skipped_count += 1
            else:
                if assign_backup_policy(vol_id, BACKUP_POLICY_OCID):
                    success_count += 1
                    status = "Sucesso"
                else:
                    failed_count += 1
                    status = "Falha na associação"
            
            output.append({
                "Volume Name": vol_name,
                "Volume OCID": vol_id,
                "Size (GB)": volume.size_in_gbs,
                "State": volume.lifecycle_state,
                "Status": status
            })

        # Gera relatório
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        csv_file = f"backup_assignment_report_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if output:
                writer = csv.DictWriter(f, fieldnames=output[0].keys())
                writer.writeheader()
                writer.writerows(output)
        
        print(f"\n✅ Relatório gerado: {csv_file}")

        print(f"\n📊 Resumo final:")
        print(f"   Volumes processados: {len(volumes)}")
        print(f"   Associações bem-sucedidas: {success_count}")
        print(f"   Volumes ignorados: {skipped_count}")
        print(f"   Falhas na associação: {failed_count}")

    except Exception as e:
        print(f"\n❌ {str(e)}")
        print("Operação interrompida devido a erro crítico")
        return

    print("\n🏁 Processo concluído com sucesso!")

if __name__ == "__main__":
    print("=" * 70)
    print(f"🚀 INICIANDO ASSOCIAÇÃO DE BACKUP PARA COMPARTMENT")
    print(f"   OCID: {COMPARTMENT_VOLUMES_OCID}")
    print("=" * 70)
    main()