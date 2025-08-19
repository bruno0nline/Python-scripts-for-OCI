import oci
import subprocess
import json
import datetime

# Nome do compartimento e da policy alvo
compartment_name = "ClientesAutcom1"
target_policy_name = "TESTE_RETENTION"

# Configuração OCI
config = oci.config.from_file()
identity_client = oci.identity.IdentityClient(config)

# Obter hora atual em UTC e calcular próxima hora
now_utc = datetime.datetime.utcnow()
target_hour = (now_utc.hour + 1) % 24  # Sempre próxima hora

print(f"⏰ Hora atual UTC: {now_utc.hour:02d}:{now_utc.minute:02d}")
print(f"🎯 Definindo backup para próxima hora cheia: {target_hour:02d}:00 UTC")

# Função para obter OCID do compartimento
def get_compartment_ocid(compartment_name, identity_client, tenancy_id):
    compartments = oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ANY"
    ).data

    for compartment in compartments:
        if compartment.name == compartment_name and compartment.lifecycle_state == "ACTIVE":
            return compartment.id
    return None

# Obter OCID do Tenancy
tenancy_id = config["tenancy"]

# Obter OCID do compartimento
compartment_ocid = get_compartment_ocid(compartment_name, identity_client, tenancy_id)

if not compartment_ocid:
    print(f"❌ ERRO: Compartimento '{compartment_name}' não encontrado ou inativo")
    exit(1)

# Comando para listar policies
cmd_list = [
    "oci", "bv", "volume-backup-policy", "list",
    "--compartment-id", compartment_ocid,
    "--output", "json"
]

# Executar comando
result = subprocess.run(cmd_list, capture_output=True, text=True)

if result.returncode != 0:
    print(f"❌ ERRO na execução do OCI CLI: {result.stderr}")
    exit(1)

try:
    policies = json.loads(result.stdout)
except json.JSONDecodeError:
    print("❌ ERRO: Falha ao decodificar resposta JSON")
    exit(1)

# Buscar e atualizar a policy
policy_updated = False
for policy in policies.get('data', []):
    if policy.get('display-name') == target_policy_name:
        print("\n🔍 Policy encontrada:")
        print(f"   Nome: {policy['display-name']}")
        print(f"   OCID: {policy['id']}")
        
        # Preparar novo schedule
        new_schedules = []
        needs_update = False
        
        for schedule in policy.get('schedules', []):
            current_hour = schedule.get('hour-of-day', -1)
            
            if current_hour != target_hour:
                print(f"   ⚠️  Horário atual: {current_hour:02d}:00 | Novo horário: {target_hour:02d}:00")
                schedule['hour-of-day'] = target_hour
                needs_update = True
            else:
                print(f"   ✅ Horário já configurado: {target_hour:02d}:00 (sem alteração necessária)")
            
            new_schedules.append(schedule)
        
        if not needs_update:
            print("ℹ️  Nenhuma atualização necessária")
            policy_updated = True
            break
        
        # Atualizar a policy
        cmd_update = [
            "oci", "bv", "volume-backup-policy", "update",
            "--policy-id", policy['id'],
            "--schedules", json.dumps(new_schedules),
            "--force"
        ]
        
        update_result = subprocess.run(cmd_update, capture_output=True, text=True)
        
        if update_result.returncode == 0:
            print("\n✅ POLÍTICA ATUALIZADA COM SUCESSO!")
            print(f"   Novo horário de backup: {target_hour:02d}:00 UTC")
            policy_updated = True
        else:
            print(f"\n❌ FALHA NA ATUALIZAÇÃO: {update_result.stderr}")
        
        break

if not policy_updated:
    print(f"\n❌ Policy '{target_policy_name}' não encontrada ou não atualizada")