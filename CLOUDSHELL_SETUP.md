# 🚀 Setup Rápido no OCI Cloud Shell

## Método 1: Instalação Automática (Recomendado)

### Passo Único - Copie e cole no Cloud Shell:

```bash
curl -sSL https://raw.githubusercontent.com/bruno0nline/Python-scripts-for-OCI/main/install.sh | bash
```

Isso vai:
- ✅ Clonar o repositório
- ✅ Instalar dependências
- ✅ Criar aliases úteis
- ✅ Deixar tudo pronto para usar

---

## Método 2: Instalação Manual (3 comandos)

```bash
# 1. Clonar o repositório
git clone https://github.com/bruno0nline/Python-scripts-for-OCI.git
cd Python-scripts-for-OCI

# 2. Instalar dependências
pip3 install --user -r requirements.txt

# 3. Pronto! Executar scripts
python3 inventory/oci-inventory-complete-report.py
```

---

## 🎯 Uso Rápido - Principais Comandos

### Listar Instâncias (CLI - mais rápido)
```bash
oci compute instance list --all --compartment-id-in-subtree true --output table
```

### Relatório Completo com Tags
```bash
cd Python-scripts-for-OCI
python3 inventory/oci-inventory-complete-report.py
```
📄 Gera: `oci_instances_full_report_with_tags.csv`

### Análise Multi-Região com Backups
```bash
python3 inventory/oci-inventory-with-backups-all-regions.py
```
📄 Gera: `oci_instances_volumes_all_regions.csv`

### Validar Políticas de Backup
```bash
python3 backup/oci-backup-policy-validator.py
```

---

## 💡 Dicas para Cloud Shell

### 1. Criar Aliases (facilita muito!)
```bash
# Adicionar ao ~/.bashrc para usar sempre
cat >> ~/.bashrc << 'EOF'

# Aliases OCI Scripts
alias oci-scripts='cd ~/Python-scripts-for-OCI'
alias oci-list='python3 ~/Python-scripts-for-OCI/inventory/oci-inventory-complete-report.py'
alias oci-backup='python3 ~/Python-scripts-for-OCI/backup/oci-backup-policy-validator.py'
alias oci-regions='python3 ~/Python-scripts-for-OCI/inventory/oci-inventory-with-backups-all-regions.py'
EOF

# Recarregar
source ~/.bashrc
```

Depois é só usar:
```bash
oci-list        # Gera relatório completo
oci-backup      # Valida backups
oci-regions     # Análise multi-região
```

### 2. Download de Arquivos CSV
```bash
# No Cloud Shell, clique no menu (⋮) > Download
# Ou use o comando:
cat oci_instances_full_report_with_tags.csv
```

### 3. Executar em Background
```bash
# Para scripts que demoram
nohup python3 inventory/oci-inventory-with-backups-all-regions.py > output.log 2>&1 &

# Ver progresso
tail -f output.log
```

### 4. Agendar Execução Diária
```bash
# Adicionar ao crontab
crontab -e

# Executar todo dia às 2h da manhã
0 2 * * * cd ~/Python-scripts-for-OCI && python3 inventory/oci-inventory-complete-report.py
```

---

## 📦 Verificar Instalação

```bash
# Verificar se está instalado
cd ~/Python-scripts-for-OCI && ls -la

# Verificar dependências
pip3 list | grep -E "oci|pandas|openpyxl"

# Testar um script rápido
python3 -c "import oci; print('✅ OCI SDK instalado com sucesso!')"
```

---

## 🔄 Atualizar Scripts

```bash
cd ~/Python-scripts-for-OCI
git pull origin main
```

---

## 🆘 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'oci'"
```bash
pip3 install --user oci pandas openpyxl
```

### Erro: "Permission denied"
```bash
chmod +x ~/Python-scripts-for-OCI/inventory/*.py
```

### Cloud Shell desconectou
```bash
# Reconectar e ir para o diretório
cd ~/Python-scripts-for-OCI
```

### Limpar arquivos antigos
```bash
# Remover CSVs antigos
rm -f *.csv *.xlsx

# Limpar logs
rm -f logs/*.log
```

---

## 📊 Workflows Prontos

### Workflow 1: Auditoria Rápida
```bash
cd ~/Python-scripts-for-OCI

# Inventário
python3 inventory/oci-inventory-complete-report.py

# Backups
python3 backup/oci-backup-policy-validator.py

# Segurança
python3 security/oci-iam-audit-report.py
```

### Workflow 2: Análise de Custos
```bash
cd ~/Python-scripts-for-OCI

# Recursos não utilizados
python3 finops/oci-finops-unused-resources.py

# Análise de volumes
python3 volumes/oci-volume-iops-analyzer.py
```

---

## 🎓 Exemplos Práticos

### Listar apenas instâncias em execução
```bash
python3 inventory/oci-inventory-complete-report.py
grep "RUNNING" oci_instances_full_report_with_tags.csv
```

### Contar instâncias por compartment
```bash
python3 inventory/oci-inventory-complete-report.py
cut -d',' -f2 oci_instances_full_report_with_tags.csv | sort | uniq -c
```

### Buscar instâncias específicas
```bash
python3 inventory/oci-inventory-complete-report.py
grep -i "producao" oci_instances_full_report_with_tags.csv
```

---

## 📝 Notas Importantes

1. **Cloud Shell tem timeout**: Sessões inativas são encerradas após 20 minutos
2. **Armazenamento persistente**: Arquivos em `~/` são mantidos entre sessões
3. **Sem configuração necessária**: Cloud Shell já está autenticado
4. **Região padrão**: Cloud Shell usa a região onde foi aberto
5. **Limites**: 5GB de armazenamento no home directory

---

## 🔗 Links Úteis

- **Repositório**: https://github.com/bruno0nline/Python-scripts-for-OCI
- **Documentação OCI CLI**: https://docs.oracle.com/en-us/iaas/tools/oci-cli/
- **OCI Python SDK**: https://docs.oracle.com/en-us/iaas/tools/python/

---

## ✅ Checklist de Primeiro Uso

- [ ] Clonar repositório no Cloud Shell
- [ ] Instalar dependências (`pip3 install -r requirements.txt`)
- [ ] Testar script básico (`python3 inventory/oci-inventory-complete-report.py`)
- [ ] Criar aliases no `~/.bashrc` (opcional)
- [ ] Fazer download do primeiro CSV gerado
- [ ] Marcar repositório como favorito no GitHub

Pronto para usar! 🎉
