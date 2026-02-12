# 🚀 Exemplos Práticos de Uso

## 📋 Cenários Comuns no Cloud Shell

### 1️⃣ Listar Todas as Instâncias (Rápido)

**Usando CLI (mais rápido):**
```bash
oci compute instance list --all --compartment-id-in-subtree true --output table
```

**Usando Python (mais detalhado):**
```bash
python3 inventory/oci-inventory-complete-report.py
```
📄 Gera: `oci_instances_full_report_with_tags.csv`

---

### 2️⃣ Verificar Backups em Todas as Regiões

```bash
python3 inventory/oci-inventory-with-backups-all-regions.py
```
📄 Gera: `oci_instances_volumes_all_regions.csv`

Este script:
- Varre todas as regiões ativas
- Lista instâncias com seus volumes
- Mostra backups associados
- Inclui boot e block volumes

---

### 3️⃣ Validar Políticas de Backup

```bash
python3 backup/oci-backup-policy-validator.py
```

Verifica:
- Instâncias sem política de backup
- Volumes sem backup configurado
- Idade dos últimos backups
- Conformidade com políticas

---

### 4️⃣ Análise de Backups Existentes

```bash
python3 backup/oci-backup-analyzer.py
```
📄 Gera: `oci_instances_backup_policies_report.csv`

Analisa:
- Políticas aplicadas
- Frequência de backups
- Retenção configurada
- Volumes sem proteção

---

### 5️⃣ Listar Apenas Block Volumes

```bash
python3 volumes/oci-volume-block-list.py
```

Lista todos os block volumes com:
- Nome e OCID
- Tamanho (GB)
- Estado
- Compartment

---

### 6️⃣ Análise de IOPS dos Discos

```bash
python3 volumes/oci-volume-iops-analyzer.py
```

Analisa performance:
- IOPS configurados
- Throughput
- Tipo de volume
- Recomendações de otimização

---

### 7️⃣ Relatório de Versões de SO

```bash
python3 os-reports/oci-os-version-report.py
```

Lista:
- Sistema operacional de cada instância
- Versão do SO
- Imagem utilizada
- Necessidade de atualização

---

### 8️⃣ Auditoria de Segurança IAM

```bash
python3 security/oci-iam-audit-report.py
```

Verifica:
- Usuários e grupos
- Políticas aplicadas
- Permissões excessivas
- Conformidade de segurança

---

### 9️⃣ Exportar Políticas IAM

```bash
python3 security/oci-iam-policy-exporter.py
```
📄 Gera: `tenancy_policies.xlsx`

Exporta:
- Todas as políticas IAM
- Statements detalhados
- Compartments associados
- Formato Excel para análise

---

### 🔟 Identificar Recursos Não Utilizados (FinOps)

```bash
python3 finops/oci-finops-unused-resources.py
```

Identifica:
- Instâncias paradas há muito tempo
- Volumes desanexados
- IPs públicos não utilizados
- Oportunidades de economia

---

## 🔧 Operações de Backup

### Criar Backup de Boot Volume

```bash
python3 backup/oci-backup-boot-volume-create.py
```

Configurações no script:
- `COMPARTMENT_NAME` - Nome do compartment
- `RETENCAO_DIAS` - Dias de retenção
- `ENABLE_EMAIL_ALERTS` - Alertas por email

### Criar Backup de Block Volume

```bash
python3 backup/oci-backup-block-volume-create.py
```

Similar ao boot volume, mas para block volumes anexados.

### Atualizar Política de Backup

```bash
python3 backup/oci-backup-policy-update.py
```

Permite:
- Alterar horário de backup
- Modificar retenção
- Atualizar frequência

### Associar Política a Block Volumes

```bash
python3 backup/oci-backup-policy-associate-block-volumes.py
```

Associa uma política de backup existente a múltiplos volumes.

---

## 🗑️ Limpeza de Backups Antigos

### Remover Backups de Boot Volumes

```bash
python3 cleanup/oci-cleanup-boot-volume-backups.py
```

⚠️ **CUIDADO**: Este script remove backups permanentemente!

Configurações:
- `CONFIRMAR_EXCLUSAO` - True para pedir confirmação
- Filtros por data
- Filtros por compartment

### Remover Backups de Block Volumes

```bash
python3 cleanup/oci-cleanup-block-volume-backups.py
```

Similar ao boot volume, mas para block volumes.

---

## 🌐 Análise de Rede

### Coletar Informações de VCNs

```bash
python3 network/oci-network-vcn-collector.py
```

Coleta:
- VCNs e subnets
- Route tables
- Security lists
- Gateways

### Relatório de Network Security Groups

```bash
python3 network/oci-compute-nsg-report.py
```

Lista:
- NSGs configurados
- Regras de segurança
- Instâncias associadas
- Portas abertas

---

## 🗄️ Inventário de Banco de Dados

```bash
python3 database/oci-database-inventory.py
```

Lista:
- DB Systems
- Autonomous Databases
- Versões e configurações
- Backups configurados

---

## 💡 Dicas de Uso

### Executar em Background
```bash
nohup python3 inventory/oci-inventory-with-backups-all-regions.py > output.log 2>&1 &
```

### Agendar Execução (Cron)
```bash
# Executar todo dia às 2h da manhã
0 2 * * * cd /caminho/scripts && python3 inventory/oci-inventory-complete-report.py
```

### Filtrar Saída CSV
```bash
# Listar apenas instâncias em execução
python3 inventory/oci-inventory-complete-report.py
grep "RUNNING" oci_instances_full_report_with_tags.csv
```

### Combinar com CLI
```bash
# Obter OCID de um compartment
COMP_ID=$(oci iam compartment list --all --query "data[?name=='MeuCompartment'].id | [0]" --raw-output)

# Usar em script Python (editar o script antes)
echo "COMPARTMENT_OCID = '$COMP_ID'" >> backup/oci-backup-policy-associate-block-volumes.py
```

---

## 📊 Análise de Resultados

### Abrir CSV no Cloud Shell
```bash
# Visualizar primeiras linhas
head -20 oci_instances_full_report_with_tags.csv

# Contar instâncias
wc -l oci_instances_full_report_with_tags.csv

# Buscar instâncias específicas
grep "producao" oci_instances_full_report_with_tags.csv
```

### Download de Arquivos
No Cloud Shell, use o menu de ações (⋮) e selecione "Download" para baixar os CSVs gerados.

---

## 🔍 Troubleshooting

### Erro de Permissão
```bash
# Verificar permissões do usuário
oci iam user get --user-id $(oci iam user list --query "data[0].id" --raw-output)

# Listar políticas aplicadas
python3 security/oci-iam-audit-report.py
```

### Script Muito Lento
```bash
# Executar apenas para uma região específica
# Editar o script e comentar outras regiões em regions_to_process
```

### Dependências Faltando
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt

# Verificar instalação
pip list | grep oci
```

---

## 📞 Comandos CLI Úteis

### Listar Compartments
```bash
oci iam compartment list --all --compartment-id-in-subtree true --output table
```

### Listar Regiões Ativas
```bash
oci iam region-subscription list --output table
```

### Obter Tenancy OCID
```bash
oci iam tenancy get --tenancy-id $(oci iam tenancy get --query "data.id" --raw-output)
```

### Listar Availability Domains
```bash
oci iam availability-domain list --output table
```

---

## 🎯 Workflows Recomendados

### Workflow 1: Auditoria Completa
```bash
# 1. Inventário completo
python3 inventory/oci-inventory-complete-report.py

# 2. Verificar backups
python3 backup/oci-backup-policy-validator.py

# 3. Auditoria de segurança
python3 security/oci-iam-audit-report.py

# 4. Identificar recursos não utilizados
python3 finops/oci-finops-unused-resources.py
```

### Workflow 2: Análise de Custos
```bash
# 1. Listar todos os recursos
python3 inventory/oci-inventory-with-backups-all-regions.py

# 2. Identificar recursos ociosos
python3 finops/oci-finops-unused-resources.py

# 3. Analisar volumes e IOPS
python3 volumes/oci-volume-iops-analyzer.py
```

### Workflow 3: Conformidade de Backup
```bash
# 1. Análise de backups
python3 backup/oci-backup-analyzer.py

# 2. Validar políticas
python3 backup/oci-backup-policy-validator.py

# 3. Listar backups existentes
python3 volumes/oci-volume-boot-backup-list.py
python3 volumes/oci-volume-block-backup-list.py
```

---

## 📝 Notas Importantes

1. **Sempre teste em ambiente de desenvolvimento primeiro**
2. **Scripts de limpeza são destrutivos - use com cuidado**
3. **Logs são salvos em `logs/` para auditoria**
4. **Arquivos CSV podem ser grandes em tenancies grandes**
5. **Alguns scripts podem levar vários minutos para executar**
