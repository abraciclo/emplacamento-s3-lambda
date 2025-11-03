#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Configurações
USER="mntabcl0"
PASS="kxmqnfsq"
ENDERECO="200.198.224.234"
PORTA=14879

# Diretórios locais
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMP_DIR="$BASE_DIR/temp"
INBOX_DIR="$BASE_DIR/inbox"

mkdir -p "$TEMP_DIR" "$INBOX_DIR"

# Arquivos temporários
LISTA_A="$TEMP_DIR/listaa.txt"
LISTA_B="$TEMP_DIR/listab.txt"
LISTA="$TEMP_DIR/lista.txt"

# ###################################
# Lista arquivos no servidor remoto
# ###################################
rm -f "$LISTA_A" "$LISTA_B" "$LISTA"

if ! pscp -ls -P "$PORTA" -pw "$PASS" "$USER@$ENDERECO:/hml" >"$LISTA_A" 2>/dev/null; then
  echo "[ERRO] Falha na obtenção da lista de arquivos ou não há arquivos para pegar"
  exit 1
fi

# Filtra pastas e lixo
grep -vi "directory" "$LISTA_A" | grep -vi "recibos" | grep -vi "\.\$\$\$" >"$LISTA"

if [[ ! -s "$LISTA" ]]; then
  echo "[INFO] Nenhum arquivo encontrado"
  exit 0
fi

echo "[INFO] Arquivos encontrados:"
cat "$LISTA"

# ###################################
# Loop sobre arquivos encontrados
# ###################################
while read -r line; do
  ARQ=$(echo "$line" | awk '{print $NF}')
  echo "[INFO] Baixando $ARQ..."

  # Cria placeholder ZR0
  ZR0="$TEMP_DIR/$ARQ.ZR0"
  : >"$ZR0"

  # Baixa arquivo
  RXIN_DATE=$(date '+%Y-%m-%d')
  RXIN_TIME=$(date '+%H:%M:%S')

  if ! pscp -v -scp -P "$PORTA" -pw "$PASS" "$USER@$ENDERECO:/hml/$ARQ" "$TEMP_DIR/$ARQ" >/dev/null 2>&1; then
    echo "[ERRO] Falha ao obter $ARQ"
    continue
  fi

  RXFI_DATE=$(date '+%Y-%m-%d')
  RXFI_TIME=$(date '+%H:%M:%S')

  # Verifica tamanho
  TAMANHO=$(stat -c%s "$TEMP_DIR/$ARQ")
  echo "[INFO] O tamanho de $ARQ é $TAMANHO"

  if [[ "$TAMANHO" -eq 0 ]]; then
    echo "[AVISO] Arquivo $ARQ é zero byte, será ignorado."
    rm -f "$TEMP_DIR/$ARQ"
    continue
  fi

  # Move para inbox
  if mv -f "$TEMP_DIR/$ARQ" "$INBOX_DIR/$ARQ"; then
    echo "[INFO] Arquivo $ARQ movido para inbox"
  else
    echo "[ERRO] Falha ao mover $ARQ"
    continue
  fi

  # Envia retorno zerado
  if pscp -v -scp -P "$PORTA" -pw "$PASS" "$ZR0" "$USER@$ENDERECO:/hml/$ARQ" >/dev/null 2>&1; then
    echo "[INFO] Enviado retorno zerado para $ARQ"
  else
    echo "[ERRO] Falha ao enviar retorno zerado para $ARQ"
  fi
  
  echo "0,0,0,$USER,$ENDERECO,$ARQ,$TAMANHO,$RXIN_DATE,$RXIN_TIME,$RXFI_DATE,$RXFI_TIME" >>"$BASE_DIR/scprxlog.csv"

  rm -f "$ZR0"

done <"$LISTA"

rm -f "$LISTA" "$LISTA_A" "$LISTA_B"

echo "[OK] Script finalizado."
exit 0
