# Maistro S3 Tool (AWS + OYOI/OIDC)


AWS S3 üzerinde upload/download/list/read_text/write_text/presign işlemleri yapan, Maistro SDK uyumlu bir araçtır. Kimlik doğrulama, **boto3 default credential chain** ile sağlanır; **OYOI/OIDC WebIdentity** (AssumeRoleWithWebIdentity) desteklidir.


## Kurulum


```bash
pip install maistro-s3-tool