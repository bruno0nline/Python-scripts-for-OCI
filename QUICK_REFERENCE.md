# 🚀 Referência Rápida - OCI Cloud Shell

## ⚡ Comandos CLI Mais Usados

### Listar Instâncias
```bash
# Todas as instâncias (formato tabela)
oci compute instance list --all --compartment-id-in-subtree true --output table

# Com campos específicos
oci compute instance list --all --compartment-id-in-subtree true \
  --query "data[*].{Nome:\"display-name\", Estado:\"lifecycle-state\", Shape:shape}" \
  --output table

# Apenas instâncias em execução
oci compute instance list --all --compartment-id-in-subtree true \
  --lifecycle-state RUNNING --output table

# Exportar para JSON
oci compute instance list --all --compartment-id-in-subtree true > instances.json
```

### Listar Volumes
```bash
# Boot volumes
oci bv boot-volume list --all --compartment-id-in-subtree true --output table

# Block volumes
oci bv volume list --all --compartment-id-in-subtree true --output table

# Backups de volumes
oci bv backup list --all --compartment-id-in-subtree true --output table
```

### Listar VCNs e Redes
```bash
# VCNs
oci network vcn list --all --compartment-id-in-subtree true --output table

# Subnets
oci network subnet list --all --compartment-id-in-subtree true --output table
```

### Informações da Conta
```bash
# Regiões disponíveis
oci iam region-subscription list

# Compartments
oci iam compartment list --all --compartment-id-in-subtree true

# Availability domains
oci iam availability-domain list
```

---

## 🐍 Scripts Python - Quando Usar

### Para Relatórios Completos
```bash
# Melhor para: Inventário completo com tags, IPs, volumes, backups
python3 inventory/oci-inventory-complete-report.py
```

### Para Análise Multi-Região
```bash
# Melhor para: Verificar backups em todas as regiões
python3 inventory/oci-inventory-with-backups-all-regions.py
```

### Para Relatório Rápido
```bash
# Melhor para: Visão geral rápida de instâncias e volumes
python3 inventory/oci-inventory-basic-report.py
```

---

## 💡 Dicas

1. **CLI é mais rápido** para consultas simples
2. **Python é melhor** para relatórios complexos com múltiplas APIs
3. No Cloud Shell, você já está autenticado automaticamente
4. Use `--output table` para visualização rápida
5. Use `--output json` para processar dados depois
6. Adicione `--all` para paginar automaticamente resultados grandes
7. Use `--compartment-id-in-subtree true` para buscar em todos os compartments

---

## 📝 Exemplos Práticos

### Contar instâncias por estado
```bash
oci compute instance list --all --compartment-id-in-subtree true \
  --query "data[*].\"lifecycle-state\"" --output json | \
  jq -r '.[]' | sort | uniq -c
```

### Listar apenas nomes e IPs
```bash
oci compute instance list --all --compartment-id-in-subtree true \
  --query "data[*].{Nome:\"display-name\", ID:id}" --output table
```

### Verificar instâncias sem backup policy
```bash
python3 backup/oci-backup-policy-validator.py
```
