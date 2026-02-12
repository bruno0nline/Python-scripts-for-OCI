# 📋 Mapeamento de Arquivos - Padronização Completa

## 🎯 Padrão de Nomenclatura
Todos os scripts seguem o padrão: `oci-<categoria>-<ação>-<detalhes>.py`

---

## 📂 Estrutura Organizada

### 📊 inventory/ - Inventário e Relatórios
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-inventory-collector.py` | `oci-inventory-collector.py` | ⭐ Inventário completo com Excel e gráficos |
| `oci-inventory-complete-report.py` | `oci_relatorio_inventario_completo.py` | ⭐ Relatório completo com tags em CSV |
| `oci-inventory-basic-report.py` | `relatorio_inventario.py` | Relatório básico de instâncias |
| `oci-inventory-extended-report.py` | `relatorio_inventario-versao-completa.py` | Versão estendida do inventário |
| `oci-inventory-full-report.py` | `oci_inventory_full_report.py` | Relatório completo alternativo |
| `oci-inventory-with-backups-all-regions.py` | `lista_instancias_discos-com-bkp.py` | ⭐ Lista com backups em todas regiões |

### 🔄 backup/ - Backup e Políticas
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-backup-analyzer.py` | `Analise_Backup_OCI.py` | Análise de backups |
| `oci-backup-policy-validator.py` | `lista_instancias_discos-com-bkp-VerificaPolicy.py` | Valida políticas de backup |
| `oci-backup-boot-volume-create.py` | `1-bkp_LinuxBancoBootVolume.py` | Cria backups de boot volumes |
| `oci-backup-block-volume-create.py` | `2-bkp_LinuxBancoBlockVolume.py` | Cria backups de block volumes |
| `oci-backup-policy-update.py` | `3-AlteraBackupPolicy.py` | Atualiza políticas de backup |
| `oci-backup-policy-update-linux-instances.py` | `4-AlteraBackupPolicyLinuxInstance.py` | Atualiza políticas em instâncias Linux |
| `oci-backup-policy-associate-block-volumes.py` | `5-AssociaPolicyBlock.py` | Associa políticas a block volumes |
| `oci-compute-backup-policy.py` | `oci-compute-backup-policy.py` | Gerenciamento de políticas de backup |
| `oci-storage-backup-policy-auditor.py` | `oci-storage-backup-policy-auditor.py` | Auditoria de políticas de storage |
| `oci-snapshot-windows.py` | `oci-snapshot-windows.py` | Snapshots para Windows |

### 💾 volumes/ - Volumes e Discos
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-volume-block-list.py` | `relatorio_listablockvolume.py` | Lista block volumes |
| `oci-volume-block-backup-list.py` | `relatorio_listablockvolumebkp.py` | Lista backups de block volumes |
| `oci-volume-boot-list.py` | `relatorio_listabootvolume.py` | Lista boot volumes |
| `oci-volume-boot-backup-list.py` | `relatorio_listabootvolumebkp.py` | Lista backups de boot volumes |
| `oci-volume-iops-analyzer.py` | `iopsdiscos.py` | Análise de IOPS dos discos |

### 🗑️ cleanup/ - Limpeza de Backups
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-cleanup-boot-volume-backups.py` | `1-Remover_BackupsBootVolumeV2.py` | Remove backups de boot volumes |
| `oci-cleanup-block-volume-backups.py` | `2-Remover_BackupsBlockVolumeV2.py` | Remove backups de block volumes |

### 🔐 security/ - Segurança e IAM
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-iam-auditor.py` | `oci-iam-auditor.py` | Auditoria de IAM |
| `oci-iam-audit-report.py` | `oci-iam-audit-report.py` | Relatório de auditoria IAM |
| `oci-iam-policy-exporter.py` | `oci-iam-policy-exporter.py` | Exporta políticas IAM |
| `oci-network-security-auditor.py` | `oci-network-security-auditor.py` | Auditoria de segurança de rede |
| `oci-audit-security-report.py` | `oci-audit-security-report.py` | Relatório de segurança e auditoria |

### 🌐 network/ - Rede e Conectividade
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-network-vcn-collector.py` | `oci-network-vcn-collector.py` | Coleta informações de VCNs |
| `oci-compute-nsg-report.py` | `oci-compute-nsg-report.py` | Relatório de Network Security Groups |

### 💰 finops/ - FinOps e Otimização
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-finops-unused-resources.py` | `oci-finops-unused-resources.py` | Identifica recursos não utilizados |

### 🗄️ database/ - Banco de Dados
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-database-inventory.py` | `oci-database-inventory.py` | Inventário de bancos de dados |

### 📋 os-reports/ - Relatórios de Sistema Operacional
| Nome Atual | Nome Anterior | Descrição |
|------------|---------------|-----------|
| `oci-os-version-report.py` | `relatorio_SOversion.py` | Versões de SO |
| `oci-os-version-with-tags-report.py` | `relatorio_SOversionTAG.py` | Versões de SO com tags |

---

## 🎯 Scripts Mais Usados (Recomendados)

### Para Inventário Completo:
```bash
python3 inventory/oci-inventory-complete-report.py
# Gera: oci_instances_full_report_with_tags.csv
```

### Para Análise Multi-Região:
```bash
python3 inventory/oci-inventory-with-backups-all-regions.py
# Gera: oci_instances_volumes_all_regions.csv
```

### Para Validar Políticas de Backup:
```bash
python3 backup/oci-backup-policy-validator.py
```

### Para Análise de Backups:
```bash
python3 backup/oci-backup-analyzer.py
# Gera: oci_instances_backup_policies_report.csv
```

---

## 📝 Convenções de Nomenclatura

### Prefixos por Categoria:
- `oci-inventory-*` - Scripts de inventário
- `oci-backup-*` - Scripts de backup
- `oci-volume-*` - Scripts de volumes
- `oci-cleanup-*` - Scripts de limpeza
- `oci-iam-*` - Scripts de IAM
- `oci-network-*` - Scripts de rede
- `oci-database-*` - Scripts de banco de dados
- `oci-finops-*` - Scripts de FinOps
- `oci-os-*` - Scripts de sistema operacional

### Sufixos por Ação:
- `*-list.py` - Lista recursos
- `*-report.py` - Gera relatórios
- `*-create.py` - Cria recursos
- `*-update.py` - Atualiza recursos
- `*-analyzer.py` - Analisa recursos
- `*-validator.py` - Valida configurações
- `*-auditor.py` - Auditoria
- `*-collector.py` - Coleta dados
- `*-exporter.py` - Exporta dados

---

## ✅ Status da Organização

- ✅ Todos os arquivos movidos para diretórios apropriados
- ✅ Nomenclatura padronizada seguindo padrão `oci-<categoria>-<ação>`
- ✅ Estrutura de diretórios criada
- ✅ Documentação atualizada
- ✅ Mapeamento completo criado
