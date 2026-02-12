# 📂 Estrutura Organizada - Scripts OCI

## 📊 1. Inventário e Relatórios
```
inventory/
├── oci_relatorio_inventario_completo.py    # ⭐ Relatório completo com tags
├── relatorio_inventario.py                  # Relatório básico de instâncias
├── relatorio_inventario-versao-completa.py # Versão estendida
└── lista_instancias_discos-com-bkp.py      # ⭐ Lista com backups (todas regiões)
```

## 💾 2. Volumes e Discos
```
volumes/
├── relatorio_listablockvolume.py          # Lista block volumes
├── relatorio_listablockvolumebkp.py       # Lista backups de block volumes
├── relatorio_listabootvolume.py           # Lista boot volumes
└── relatorio_listabootvolumebkp.py        # Lista backups de boot volumes
```

## 🔄 3. Backup e Políticas
```
backup/
├── Analise_Backup_OCI.py                   # Análise de backups
├── lista_instancias_discos-com-bkp-VerificaPolicy.py  # Verifica políticas
├── 1-bkp_LinuxBancoBootVolume.py          # Backup boot volumes
├── 2-bkp_LinuxBancoBlockVolume.py         # Backup block volumes
├── 3-AlteraBackupPolicy.py                 # Altera políticas
├── 4-AlteraBackupPolicyLinuxInstance.py   # Altera políticas em instâncias
└── 5-AssociaPolicyBlock.py                # Associa políticas
```

## 🗑️ 4. Limpeza
```
cleanup/
├── 1-Remover_BackupsBootVolumeV2.py       # Remove backups boot
└── 2-Remover_BackupsBlockVolumeV2.py      # Remove backups block
```

## 🔐 5. Segurança e IAM
```
security/
├── oci-iam-audit-report.py                 # Relatório auditoria IAM
├── oci-iam-policy-exporter.py             # Exporta políticas IAM
└── oci-network-security-auditor.py        # Auditoria segurança rede
```

## 🌐 6. Rede
```
network/
└── oci-network-vcn-collector.py           # Coleta informações VCNs
```

## 💰 7. FinOps
```
finops/
└── oci-finops-unused-resources.py         # Recursos não utilizados
```

## 📋 8. Sistema Operacional
```
os-reports/
├── relatorio_SOversion.py                  # Versões de SO
└── relatorio_SOversionTAG.py              # Versões de SO com tags
```

---

## 🎯 Comandos Recomendados

### Para listar instâncias rapidamente no Cloud Shell:

```bash
# Comando CLI mais rápido (recomendado)
oci compute instance list --all --compartment-id-in-subtree true --output table

# Com filtros específicos
oci compute instance list --all --compartment-id-in-subtree true \
  --query "data[*].{Nome:\"display-name\", Estado:\"lifecycle-state\", Shape:shape, Compartment:\"compartment-id\"}" \
  --output table
```

### Scripts Python recomendados:

```bash
# 1. Relatório completo com tags (MELHOR OPÇÃO)
python3 oci_relatorio_inventario_completo.py
# Gera: oci_instances_full_report_with_tags.csv

# 2. Lista com backups em todas regiões
python3 lista_instancias_discos-com-bkp.py
# Gera: oci_instances_volumes_all_regions.csv

# 3. Relatório básico rápido
python3 relatorio_inventario.py
# Gera: oci_instances_full_report.csv
```
