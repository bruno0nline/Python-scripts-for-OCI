#!/usr/bin/env python3
"""
Script para listar instâncias nas regiões do Brasil (São Paulo e Vinhedo)
Gera um CSV com todas as instâncias encontradas em ambas as regiões
"""

import oci
import csv
import sys

print("=" * 60)
print("🇧🇷 Inventário OCI - Regiões Brasil")
print("=" * 60)
print()

# Regiões do Brasil
BRAZIL_REGIONS = [
    'sa-saopaulo-1',  # Brazil East (São Paulo)
    'sa-vinhedo-1',   # Brazil Southeast (Vinhedo)
]

# Carrega configuração do OCI
try:
    config = oci.config.from_file()
    pri