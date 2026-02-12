# ⚡ Quick Start - OCI Cloud Shell

## 🎯 Instalação em 1 Comando

Abra o Cloud Shell e execute:

```bash
curl -sSL https://raw.githubusercontent.com/bruno0nline/Python-scripts-for-OCI/main/install.sh | bash
```

Depois ative os aliases:
```bash
source ~/.bashrc
```

Pronto! ✅

---

## 🚀 Uso Imediato

### Opção 1: Usar Aliases (Mais Fácil)

```bash
oci-list      # Relatório completo de instâncias
oci-backup    # Validar políticas de backup
oci-regions   # Análise multi-região
oci-help      # Ver documentação
```

### Opção 2: Comandos Diretos

```bash
cd ~/Python-scripts-for-OCI

# Relatório completo
python3 inventory/oci-inventory-complete-report.py

# Validar backups
python3 backup/oci-backup-policy-validator.py

# Multi-região
python3 inventory/oci-inventory-with-backups-all-regions.py
```

### Opção 3: CLI Nativo (Mais Rápido)

```bash
# Listar instâncias
oci compute instance list --all --compartment-id-in-subtree true --output table

# Listar volumes
oci bv volume list --all --compartment-id-in-subtree true --output table
```

---

## 📥 Download de Resultados

Após executar um script, faça download do CSV:

1. No Cloud Shell, clique no menu **⋮** (três pontos)
2. Selecione **Download**
3. Digite o nome do arquivo: `oci_instances_full_report_with_tags.csv`

Ou visualize no terminal:
```bash
cat oci_instances_full_report_with_tags.csv | head -20
```

---

## 🔄 Atualizar Scripts

```bash
cd ~/Python-scripts-for-OCI
git pull
```

---

## 📚 Documentação Completa

- **CLOUDSHELL_SETUP.md** - Guia completo de instalação e uso
- **USAGE_EXAMPLES.md** - Exemplos práticos de todos os scripts
- **QUICK_REFERENCE.md** - Referência rápida de comandos CLI
- **README.md** - Documentação geral do projeto

---

## 💡 Dica Pro

Adicione ao seu `~/.bashrc` para sempre ter acesso rápido:

```bash
echo 'alias oci="cd ~/Python-scripts-for-OCI"' >> ~/.bashrc
source ~/.bashrc
```

Agora é só digitar `oci` e você está no diretório! 🎉
