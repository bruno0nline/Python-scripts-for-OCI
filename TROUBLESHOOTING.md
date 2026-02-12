# 🔧 Troubleshooting - Problemas Comuns

## ❌ Erro: "ServiceError: identity not found"

### Causa
Script não consegue autenticar com a OCI.

### ✅ Solução
Atualize o repositório (scripts foram corrigidos):
```bash
cd ~/Python-scripts-for-OCI
git pull origin main
```

---

## ❌ Erro: "ModuleNotFoundError: No module named 'oci'"

### ✅ Solução
```bash
pip3 install --user oci pandas openpyxl
```

---

## ❌ Erro: "Permission denied"

### ✅ Solução
Verifique permissões IAM:
```bash
oci iam user get --user-id $(oci iam user list --query "data[0].id" --raw-output)
```

Você precisa de políticas como:
- `Allow group <grupo> to read all-resources in tenancy`
- `Allow group <grupo> to manage instance-family in tenancy`

---

## ❌ Script não encontra instâncias

### Possíveis Causas

**1. Região errada**
```bash
# Ver regiões disponíveis
oci iam region-subscription list

# Editar script e ajustar região
nano inventory/oci-inventory-basic-report.py
# Descomentar: config['region'] = 'sa-saopaulo-1'
```

**2. Instâncias em outro compartment**
```bash
# Listar compartments
oci iam compartment list --all --output table

# Testar CLI
oci compute instance list --all --compartment-id-in-subtree true
```

---

## ❌ Cloud Shell desconectou

### ✅ Solução
Execute em background:
```bash
nohup python3 inventory/oci-inventory-basic-report.py > output.log 2>&1 &
tail -f output.log
```

---

## ❌ Erro: "rate limit exceeded"

### ✅ Solução
Aguarde alguns minutos ou comente regiões no script:
```python
regions_to_process = [
    'sa-saopaulo-1',  # Apenas uma região
]
```

---

## 💡 Dicas de Debug

### Ver logs detalhados
```bash
python3 inventory/oci-inventory-basic-report.py 2>&1 | tee debug.log
```

### Testar autenticação
```bash
oci iam region list
oci iam compartment list --all
```

### Verificar instalação
```bash
python3 -c "import oci; print('✅ OCI SDK OK')"
pip3 list | grep -E "oci|pandas"
```

---

## 🆘 Ainda com problemas?

1. Verifique se está no Cloud Shell (não terminal local)
2. Atualize o repositório: `git pull`
3. Reinstale dependências: `pip3 install --user -r requirements.txt`
4. Teste com CLI primeiro: `oci compute instance list --all`
5. Verifique permissões IAM no console OCI
