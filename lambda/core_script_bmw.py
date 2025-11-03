import os
import boto3
import paramiko
from datetime import datetime

S3_BUCKET = "bmws3buckets"
SFTP_HOST = "15.229.38.208"
SFTP_PORT = 22
SFTP_USER = "ubuntu"
PRIVATE_KEY_PATH = "bmwwinscp.pem"
# PASSPHRASE = "sua_senha_se_tiver"

# Mapeamento dos meses em português
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

def lambda_handler(event, context):
    year = event.get("year") or datetime.now().year
    month_num = event.get("month") or datetime.now().month
    month_name = MESES_PT.get(int(month_num))
    
    print(f"[INFO] Processando arquivos do S3: {year}/{month_name}")
    
    tmp_dir = "/tmp/inbox"
    os.makedirs(tmp_dir, exist_ok=True)
    
    s3_prefix = f"{year}/{month_name}/"
    
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    files = []
    
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=s3_prefix):
        contents = page.get('Contents', [])
        if not contents:
            print("[INFO] Página sem conteúdo")
        for obj in contents:
            key = obj['Key']
            print(f"[DEBUG] Arquivo no bucket: {key}")
            if key.endswith('/'):
                continue
            filename = os.path.basename(key)
            fname_upper = filename.upper()
            if "DT" in fname_upper or "DN" in fname_upper:
                local_path = os.path.join(tmp_dir, filename)
                s3.download_file(S3_BUCKET, key, local_path)
                files.append(local_path)
                print(f"[S3] Baixado {key}")
    
    if not files:
        print("[INFO] Nenhum arquivo com 'DT' ou 'DN' encontrado no S3")
        return
    
    key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_PATH)  # adicione password=PASSPHRASE se precisar
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, pkey=key)
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_path = f"{year}/{month_name}"  # Ex: "2025/Outubro"
    parts = remote_path.strip("/").split("/")

    # Cria diretórios de forma progressiva, um por um
    for p in parts:
        try:
            sftp.chdir(p)  # tenta entrar no diretório
        except IOError:
            print(f"[DEBUG] Criando diretório: {p}")
            sftp.mkdir(p)  # cria o diretório no nível atual
            sftp.chdir(p)  # entra nele após criar
        print(f"[DEBUG] Agora em: {sftp.getcwd()}")  # mostra onde está

    # Envia os arquivos
    for file_path in files:
        filename = os.path.basename(file_path)
        remote_file = filename  # já está no diretório certo
        try:
            sftp.put(file_path, remote_file)
            print(f"[SFTP] Arquivo enviado: {filename}")
            key_to_delete = f"{s3_prefix}{filename}"

            try:
                s3.delete_object(Bucket=S3_BUCKET, Key=key_to_delete)
                print(f"[S3] Arquivo removido do S3: {key_to_delete}")
            except Exception as delete_err:
                print(f"[ERRO] Falha ao remover {key_to_delete} do S3: {delete_err}")

        except Exception as upload_err:
            print(f"[ERRO] Falha ao enviar {filename} via SFTP: {upload_err}")

    sftp.close()
    transport.close()
    print("[INFO] Todos os arquivos processados com sucesso.")
    

