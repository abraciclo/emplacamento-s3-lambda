import boto3
import os
from datetime import datetime

# ✅ Mapeamento dos meses em português
MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

# ✅ Buckets de origem e destino
SOURCE_BUCKET = "hondas3bucket"
DEST_BUCKET = "bmwabraciclo"
DEST_PREFIX_BASE = "ABRACICLO"

# ✅ Limite de arquivos por execução (opcional)
MAX_FILES = 20  # pode ajustar ou remover se quiser processar tudo

def lambda_handler(event, context=None):
    # 📅 Ano e mês
    year = int(event.get("year", datetime.now().year))
    month_num = int(event.get("month", datetime.now().month))
    month_name = MESES_PT.get(month_num)

    if not month_name:
        print(f"[ERRO] Mês inválido: {month_num}")
        return

    print(f"[INFO] Processando arquivos de {SOURCE_BUCKET}: {year}/{month_name}")

    # 📁 Diretório temporário
    tmp_dir = "/tmp/inbox"
    os.makedirs(tmp_dir, exist_ok=True)

    # 🔍 Prefixos
    source_prefix = f"{year}/{month_name}/"
    dest_prefix = f"{DEST_PREFIX_BASE}/{year}/{month_name}/"

    s3 = boto3.client('s3')
    arquivos_processados = []
    file_count = 0

    try:
        print(f"[DEBUG] Listando objetos com prefixo: {source_prefix}")
        response = s3.list_objects_v2(Bucket=SOURCE_BUCKET, Prefix=source_prefix)

        contents = response.get("Contents", [])
        print(f"[DEBUG] Total de objetos encontrados: {len(contents)}")

        for obj in contents:
            key = obj["Key"]
            print(f"[DEBUG] Verificando objeto: {key}")

            if key.endswith("/"):
                print(f"[SKIP] Ignorando pasta: {key}")
                continue

            filename = os.path.basename(key)
            fname_upper = filename.upper()

            if "DT" in fname_upper or "DN" in fname_upper:
                if file_count >= MAX_FILES:
                    print(f"[INFO] Limite de {MAX_FILES} arquivos atingido")
                    break

                local_path = os.path.join(tmp_dir, filename)

                try:
                    print(f"[DOWNLOAD] Baixando {key} para {local_path}")
                    s3.download_file(SOURCE_BUCKET, key, local_path)
                    print(f"[DOWNLOAD] Sucesso: {key}")

                    dest_key = f"{dest_prefix}{filename}"
                    print(f"[UPLOAD] Enviando para s3://{DEST_BUCKET}/{dest_key}")
                    s3.upload_file(local_path, DEST_BUCKET, dest_key)
                    print(f"[UPLOAD] Sucesso: {dest_key}")

                    arquivos_processados.append({
                        "arquivo": filename,
                        "origem": key,
                        "destino": dest_key
                    })

                    try:
                        print(f"[DELETE] Removendo arquivo de origem: {key}")
                        s3.delete_object(Bucket=SOURCE_BUCKET, Key=key)
                        print(f"[DELETE] Sucesso ao remover: {key}")
                    except Exception as delete_error:
                        print(f"[ERRO] Falha ao remover {key} do bucket de origem: {delete_error}")

                    arquivos_processados.append({
                        "arquivo": filename,
                        "origem": key,
                        "destino": dest_key
                    })

                    file_count += 1
                except Exception as file_error:
                    print(f"[ERRO] Falha ao processar arquivo {key}: {file_error}")
                    continue
                
                

    except Exception as e:
        print(f"[ERRO] Falha geral durante a execução: {e}")
        return

    if not arquivos_processados:
        print("[INFO] Nenhum arquivo com 'DT' ou 'DN' encontrado")
    else:
        print(f"[INFO] {len(arquivos_processados)} arquivos processados com sucesso")

    return {
        "total": len(arquivos_processados),
        "arquivos": arquivos_processados
    }


