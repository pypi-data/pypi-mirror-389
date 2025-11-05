import os
import json
import pytest
from moto import mock_aws
import boto3
from maistro_s3_tool.tool import S3Tool

@mock_aws
def test_s3_tool_basic_flow(tmp_path):
    # Mock region + S3
    os.environ["AWS_DEFAULT_REGION"] = "eu-central-1"
    s3 = boto3.client("s3")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)


    tool = S3Tool()


    # write_text
    res = json.loads(tool._run(action="write_text", bucket=bucket, key="dir/hello.txt", content="merhaba"))
    assert res.get("status") == "success"


    # read_text
    res = json.loads(tool._run(action="read_text", bucket=bucket, key="dir/hello.txt"))
    assert res.get("content") == "merhaba"


    # upload (lokal dosyadan)
    f = tmp_path / "lokal.txt"
    f.write_text("lokal-icerik", encoding="utf-8")
    res = json.loads(tool._run(action="upload", bucket=bucket, key="dir/lokal.txt", file_path=str(f)))
    assert res.get("status") == "success"


    # list
    res = json.loads(tool._run(action="list", bucket=bucket, prefix="dir/"))
    assert res.get("status") == "success"
    assert any(i["key"] == "dir/lokal.txt" for i in res["items"])


    # download (lokale indir)
    out = tmp_path / "indirilen.txt"
    res = json.loads(tool._run(action="download", bucket=bucket, key="dir/hello.txt", file_path=str(out)))
    assert res.get("status") == "success"
    assert out.read_text(encoding="utf-8") == "merhaba"


    # presign
    res = json.loads(tool._run(action="presign", bucket=bucket, key="dir/hello.txt", expires_in=60))
    assert res.get("status") == "success"
    assert "url" in res