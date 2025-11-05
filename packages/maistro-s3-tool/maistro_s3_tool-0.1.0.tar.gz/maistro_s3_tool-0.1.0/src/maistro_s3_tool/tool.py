# src/s3_reader_tool/s3_reader_tool.py

from __future__ import annotations

import json
import os
import csv
from io import StringIO, BytesIO
from typing import Any, Optional, Tuple

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from maistro.core.base_tool import CustomBaseTool

try:
    import requests  # presigned URL indirme için
except Exception:
    requests = None

try:
    from docx import Document
    _HAS_DOCX = True
except Exception:
    _HAS_DOCX = False


class S3ReaderTool(CustomBaseTool):
    """
    Read-only, multi-format S3/MinIO reader.

    Öncelik: download_url -> yoksa S3/MinIO (bucket/object)

    Çıktı sözleşmesi:
      - CSV  : list[dict]                (CsvTool ile bire bir)
      - JSON : dict/list                 (passthrough)
      - DOCX/TXT/MD/LOG/XML/HTML/… : {"content": "<metin>"}
    """

    def __init__(self) -> None:
        super().__init__(
            name="s3_reader_tool",
            description=(
                "Reads files from presigned URL or S3/MinIO (fallback). "
                "CSV→list[dict], JSON→parsed, others→plain text."
            ),
        )

    def _run(
        self,
        action: str,
        download_url: Optional[str] = None,
        bucket_name: Optional[str] = None,
        object_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        use_path_style: bool = True,
        document_type: Optional[str] = None,
        timeout_sec: int = 30,
        try_json_on_unknown: bool = True,
        max_bytes: Optional[int] = None,
        **_: Any
    ) -> str:
        if action != "read":
            return json.dumps({"error": "Only 'read' action is supported."}, ensure_ascii=False)

        try:
            # 1) İçeriği getir (presigned URL öncelikli)
            body: Optional[bytes] = None
            source_hint: Optional[str] = None
            content_type: Optional[str] = None
            content_encoding: Optional[str] = None

            if download_url:
                if not requests:
                    return json.dumps(
                        {"error": "requests module not available for download_url."},
                        ensure_ascii=False,
                    )
                resp = requests.get(download_url, timeout=timeout_sec)
                resp.raise_for_status()
                body = resp.content
                source_hint = download_url.split("?")[0]
                content_type = resp.headers.get("Content-Type")
                content_encoding = resp.headers.get("Content-Encoding")

            if body is None:
                # 2) S3/MinIO üzerinden oku
                if not bucket_name or not object_name:
                    return json.dumps(
                        {"error": "Provide download_url or (bucket_name & object_name)."},
                        ensure_ascii=False,
                    )
                s3 = self._client(
                    endpoint_url=endpoint_url,
                    region_name=region_name,
                    access_key_id=access_key_id,
                    secret_access_key=secret_access_key,
                    use_path_style=use_path_style,
                )
                obj = s3.get_object(Bucket=bucket_name, Key=object_name)
                # Savunmacı: büyük dosyalar için limit
                if max_bytes is not None and max_bytes > 0:
                    body = obj["Body"].read(max_bytes)
                else:
                    body = obj["Body"].read()
                source_hint = object_name
                content_type = obj.get("ContentType")
                content_encoding = obj.get("ContentEncoding")

            # 3) Tür & uzantı belirleme
            ext = self._infer_extension(document_type, source_hint, content_type)

            # 4) İçerik kod çözme (gerekirse gzip vb. burada ele alınabilir)
            if content_encoding and content_encoding.lower() == "gzip":
                # Not: İhtiyaç varsa buraya gzip.decompress(body) eklenebilir.
                pass  # Şimdilik pas geçiyoruz; presigned tarafında genelde encoding yoktur.

            # 5) Format bazlı parse
            if ext == "csv":
                return json.dumps(self._parse_csv(body), ensure_ascii=False)

            if ext == "json":
                parsed = self._parse_json(body)
                if isinstance(parsed, dict) or isinstance(parsed, list):
                    return json.dumps(parsed, ensure_ascii=False)
                return json.dumps({"error": f"JSON parse error: {parsed}"}, ensure_ascii=False)

            if ext == "docx":
                text = self._read_docx(body)
                return json.dumps({"content": text}, ensure_ascii=False)

            # Metin-tabanlı diğer uzantılar veya bilinmeyen türler
            text = self._read_text(body)

            # Uzantı bilinmiyor ancak JSON olma ihtimali var: opsiyonel aggressive parse
            if ext == "" and try_json_on_unknown:
                jp = self._try_json(text)
                if jp[0]:
                    return json.dumps(jp[1], ensure_ascii=False)

            return json.dumps({"content": text}, ensure_ascii=False)

        except (BotoCoreError, ClientError) as e:
            return json.dumps({"error": f"S3 error: {str(e)}"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    async def _arun(self, *args, **kwargs) -> str:
        return self._run(*args, **kwargs)

    # ----------------------
    # Helpers
    # ----------------------

    @staticmethod
    def _client(
        endpoint_url: Optional[str],
        region_name: Optional[str],
        access_key_id: Optional[str],
        secret_access_key: Optional[str],
        use_path_style: bool,
    ):
        """
        Kimlik doğrulama stratejisi:
        - Varsayılan: boto3 default credential chain (OYOI/OIDC WebIdentity dahil).
        - access_key_id/secret_access_key verilirse yalnızca o kimlik bilgileri kullanılır.
        """
        session_kwargs = {}
        # Region için; yoksa boto3 config/env zincirine bırak
        if region_name:
            session_kwargs["region_name"] = region_name

        # NOT: Burada bilerek access keys'i Session'a enjekte ETMİYORUZ (None/boş değerler zinciri bozar).
        session = boto3.session.Session(**session_kwargs)

        client_kwargs = {
            "config": Config(signature_version="s3v4", s3={"addressing_style": "path" if use_path_style else "virtual"}),
        }
        if endpoint_url or os.getenv("S3_ENDPOINT_URL"):
            client_kwargs["endpoint_url"] = endpoint_url or os.getenv("S3_ENDPOINT_URL")

        # İsteğe bağlı: açıkça credential geçmek istenirse
        if access_key_id and secret_access_key:
            client_kwargs["aws_access_key_id"] = access_key_id
            client_kwargs["aws_secret_access_key"] = secret_access_key

        return session.client("s3", **client_kwargs)

    @staticmethod
    def _infer_extension(document_type: Optional[str], source_hint: Optional[str], content_type: Optional[str]) -> str:
        if document_type:
            return document_type.lower().strip()

        # URL/path uzantısı
        if source_hint and "." in source_hint:
            ext = source_hint.rsplit(".", 1)[-1].lower()
            # Basit normalize
            if ext in {"csv", "json", "txt", "md", "log", "xml", "html", "htm", "docx"}:
                return ext

        # Content-Type fallback
        if content_type:
            c = content_type.lower()
            if "json" in c:
                return "json"
            if "csv" in c:
                return "csv"
            if "wordprocessingml.document" in c or "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in c:
                return "docx"
            if "html" in c:
                return "html"
            if "xml" in c:
                return "xml"
            if "markdown" in c:
                return "md"
            if "text" in c:
                return "txt"
        return ""

    @staticmethod
    def _parse_json(body: bytes):
        try:
            text = body.decode("utf-8", errors="replace")
            return json.loads(text)
        except Exception as e:
            return f"{e}"

    @staticmethod
    def _parse_csv(body: bytes):
        # BOM temizliği + ayraç tespiti
        raw = body.decode("utf-8-sig", errors="replace")
        sample = raw[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample)
        except Exception:
            dialect = csv.excel
        reader = csv.DictReader(StringIO(raw), dialect=dialect)
        return [dict(r) for r in reader]

    @staticmethod
    def _read_text(body: bytes) -> str:
        try:
            return body.decode("utf-8", errors="replace")
        except Exception as e:
            return f"[decode error: {str(e)}]"

    @staticmethod
    def _read_docx(body: bytes) -> str:
        if not _HAS_DOCX:
            return "[python-docx not installed]"
        try:
            doc = Document(BytesIO(body))
            return "\n".join(p.text for p in doc.paragraphs if (p.text or "").strip())
        except Exception as e:
            return f"[DOCX parse error: {str(e)}]"

    @staticmethod
    def _try_json(text: str) -> Tuple[bool, Any]:
        try:
            return True, json.loads(text)
        except Exception:
            return False, None
