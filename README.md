# OCI Scripts - Automação e Gerenciamento
Scripts para automação e gerenciamento do Oracle Cloud Infrastructure via Cloud Shell

## 📁 Estrutura Organizada

### 📊 inventory/ - Inventário e Relatórios
- `oci-inventory-collector.py` - ⭐ Inventário completo com Excel, gráficos e validações
- `oci-inventory-complete-report.py` - ⭐ Relatório completo com tags em CSV
- `oci-inventory-basic-report.py` - Relatório básico de instâncias com volumes e IPs
- `oci-inventory-extended-report.py` - Versão estendida do inventário
- `oci-inventory-full-report.py` - Relatório completo alternativo
- `oci-inventory-with-backups-all-regions.py` - ⭐ Lista com backups (todas regiões)

### 💾 volumes/ - Volumes e Discos
- `oci-volume-block-list.py` - Lista block volumes
- `oci-volume-block-backup-list.py` - Lista backups de block volumes
- `oci-volume-boot-list.py` - Lista boot volumes
- `oci-volume-boot-backup-list.py` - Lista backups de boot volumes
- `oci-volume-iops-analyzer.py` - Análise de IOPS dos discos

### 🔄 backup/ - Backup e Políticas
- `oci-backup-analyzer.py` - Análise de backups
- `oci-backup-policy-validator.py` - Valida políticas de backup
- `oci-backup-boot-volume-create.py` - Cria backups de boot volumes
- `oci-backup-block-volume-create.py` - Cria backups de block volumes
- `oci-backup-policy-update.py` - Atualiza políticas de backup
- `oci-backup-policy-update-linux-instances.py` - Atualiza políticas em instâncias Linux
- `oci-backup-policy-associate-block-volumes.py` - Associa políticas a block volumes
- `oci-compute-backup-policy.py` - Gerenciamento de políticas de backup
- `oci-storage-backup-policy-auditor.py` - Auditoria de políticas de storage
- `oci-snapshot-windows.py` - Snapshots para Windows

### 🗑️ cleanup/ - Limpeza de Backups
- `oci-cleanup-boot-volume-backups.py` - Remove backups de boot volumes
- `oci-cleanup-block-volume-backups.py` - Remove backups de block volumes

### 🔐 security/ - Segurança e IAM
- `oci-iam-auditor.py` - Auditoria de IAM
- `oci-iam-audit-report.py` - Relatório de auditoria IAM
- `oci-iam-policy-exporter.py` - Exporta políticas IAM
- `oci-network-security-auditor.py` - Auditoria de segurança de rede
- `oci-audit-security-report.py` - Relatório de segurança e auditoria

### 🌐 network/ - Rede e Conectividade
- `oci-network-vcn-collector.py` - Coleta informações de VCNs
- `oci-compute-nsg-report.py` - Relatório de Network Security Groups

### 💰 finops/ - FinOps e Otimização
- `oci-finops-unused-resources.py` - Identifica recursos não utilizados

### 🗄️ database/ - Banco de Dados
- `oci-database-inventory.py` - Inventário de bancos de dados

### 📋 os-reports/ - Sistema Operacional
- `oci-os-version-report.py` - Versões de SO
- `oci-os-version-with-tags-report.py` - Versões de SO com tags

---

## 🚀 Quick Start - Listar Instâncias

### Via CLI (mais rápido)
```bash
# Listar todas as instâncias
oci compute instance list --all --compartment-id-in-subtree true --output table

# Listar com detalhes específicos
oci compute instance list --all --compartment-id-in-subtree true \
  --query "data[*].{Name:\"display-name\", State:\"lifecycle-state\", Shape:shape}" \
  --output table
```

### Via Python
```bash
# Relatório completo com tags (recomendado)
python3 inventory/oci-inventory-complete-report.py

# Inventário com Excel e gráficos
python3 inventory/oci-inventory-collector.py

# Lista com backups em todas regiões
python3 inventory/oci-inventory-with-backups-all-regions.py
```

---

## 📦 Dependências
```bash
pip install -r requirements.txt
```

Dependências necessárias:
- `oci` - SDK oficial da Oracle Cloud
- `pandas` - Manipulação de dados
- `openpyxl` - Geração de arquivos Excel

---

## ⚙️ Configuração
Os scripts usam a configuração padrão do OCI CLI em `~/.oci/config`

No Cloud Shell, a autenticação já está configurada automaticamente.

---

## 📚 Documentação Adicional

- **FILE_MAPPING.md** - Mapeamento completo de nomes antigos para novos
- **ORGANIZE.md** - Estrutura detalhada de organização
- **QUICK_REFERENCE.md** - Comandos CLI mais usados

---

## 🎯 Padrão de Nomenclatura

Todos os scripts seguem o padrão: `oci-<categoria>-<ação>-<detalhes>.py`

Exemplos:
- `oci-inventory-complete-report.py`
- `oci-backup-policy-validator.py`
- `oci-volume-iops-analyzer.py`

---

## 💡 Scripts Mais Usados

### 1. Inventário Completo
```bash
python3 inventory/oci-inventory-complete-report.py
```
Gera CSV com: nome, compartment, IPs, volumes, backups, tags, SO

### 2. Análise Multi-Região
```bash
python3 inventory/oci-inventory-with-backups-all-regions.py
```
Varre todas as regiões e lista instâncias com volumes e backups

### 3. Validar Políticas de Backup
```bash
python3 backup/oci-backup-policy-validator.py
```
Verifica se instâncias têm políticas de backup configuradas

### 4. Análise de Backups
```bash
python3 backup/oci-backup-analyzer.py
```
Analisa backups existentes e políticas aplicadas

---

## 📂 Estrutura de Diretórios

```
.
├── inventory/          # Scripts de inventário e relatórios
├── backup/            # Scripts de backup e políticas
├── volumes/           # Scripts de volumes e discos
├── cleanup/           # Scripts de limpeza
├── security/          # Scripts de segurança e IAM
├── network/           # Scripts de rede
├── database/          # Scripts de banco de dados
├── finops/            # Scripts de FinOps
├── os-reports/        # Scripts de relatórios de SO
├── logs/              # Logs de execução
└── output_file/       # Arquivos de saída gerados
```

---

## 🔧 Uso no Cloud Shell

Como você já está conectado no Cloud Shell:

1. Clone ou faça upload dos scripts
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute o script desejado: `python3 <diretorio>/<script>.py`

Não é necessário configurar credenciais - o Cloud Shell já está autenticado!

---

## ⚠️ Observações Importantes

- Alguns scripts podem levar tempo para executar em tenancies grandes
- Logs são salvos automaticamente no diretório `logs/`
- Arquivos CSV são gerados no diretório atual ou em `output_file/`
- Sempre revise os scripts antes de executar operações de modificação ou exclusão

---

## 📝 Contribuindo

Para adicionar novos scripts, siga o padrão de nomenclatura:
- Use o prefixo `oci-`
- Inclua a categoria (`inventory`, `backup`, `security`, etc)
- Descreva a ação (`list`, `report`, `create`, `update`, etc)
- Adicione documentação no cabeçalho do script
