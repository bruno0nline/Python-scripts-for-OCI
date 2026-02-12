#!/bin/bash

# Script de instalação automática para OCI Cloud Shell
# Repositório: https://github.com/bruno0nline/Python-scripts-for-OCI

set -e

echo "=================================================="
echo "🚀 Instalação Automática - OCI Python Scripts"
echo "=================================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório de instalação
INSTALL_DIR="$HOME/Python-scripts-for-OCI"

# Função para imprimir mensagens
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# 1. Verificar se já existe instalação
if [ -d "$INSTALL_DIR" ]; then
    print_warning "Diretório já existe. Atualizando..."
    cd "$INSTALL_DIR"
    git pull origin main
    print_success "Repositório atualizado!"
else
    # 2. Clonar repositório
    print_status "Clonando repositório..."
    git clone https://github.com/bruno0nline/Python-scripts-for-OCI.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    print_success "Repositório clonado!"
fi

echo ""

# 3. Instalar dependências
print_status "Instalando dependências Python..."
pip3 install --user -q oci pandas openpyxl
print_success "Dependências instaladas!"

echo ""

# 4. Criar aliases
print_status "Configurando aliases..."

# Verificar se aliases já existem
if ! grep -q "# OCI Scripts Aliases" ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# OCI Scripts Aliases
alias oci-scripts='cd ~/Python-scripts-for-OCI'
alias oci-list='cd ~/Python-scripts-for-OCI && python3 inventory/oci-inventory-complete-report.py'
alias oci-backup='cd ~/Python-scripts-for-OCI && python3 backup/oci-backup-policy-validator.py'
alias oci-regions='cd ~/Python-scripts-for-OCI && python3 inventory/oci-inventory-with-backups-all-regions.py'
alias oci-help='cat ~/Python-scripts-for-OCI/CLOUDSHELL_SETUP.md'
EOF
    print_success "Aliases criados!"
else
    print_warning "Aliases já existem no ~/.bashrc"
fi

echo ""

# 5. Criar diretório de logs se não existir
mkdir -p "$INSTALL_DIR/logs"
print_success "Diretório de logs criado!"

echo ""
echo "=================================================="
echo "✅ Instalação concluída com sucesso!"
echo "=================================================="
echo ""
echo "📚 Comandos disponíveis:"
echo ""
echo "  ${GREEN}oci-scripts${NC}  - Ir para o diretório dos scripts"
echo "  ${GREEN}oci-list${NC}     - Gerar relatório completo de instâncias"
echo "  ${GREEN}oci-backup${NC}   - Validar políticas de backup"
echo "  ${GREEN}oci-regions${NC}  - Análise multi-região com backups"
echo "  ${GREEN}oci-help${NC}     - Ver documentação completa"
echo ""
echo "🎯 Para ativar os aliases agora, execute:"
echo "  ${YELLOW}source ~/.bashrc${NC}"
echo ""
echo "📖 Ou simplesmente feche e abra o Cloud Shell novamente"
echo ""
echo "🚀 Exemplo de uso rápido:"
echo "  ${BLUE}cd ~/Python-scripts-for-OCI${NC}"
echo "  ${BLUE}python3 inventory/oci-inventory-complete-report.py${NC}"
echo ""
echo "=================================================="
