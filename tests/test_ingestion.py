from datetime import UTC, datetime

import pytest

from alphawatch.data.ingestion import BronzeWriter, ProviderResponse


def test_bronze_is_immutable_and_checksummed(tmp_path) -> None:
    response = ProviderResponse(
        b"raw-provider-bytes",
        "fixture",
        "2020-01-01",
        "2020-12-31",
        "v1",
        "1.0",
        datetime.now(UTC),
    )
    manifest = BronzeWriter(tmp_path).persist(response, "run-1")
    assert len(manifest.checksum_sha256) == 64
    payload = tmp_path / "fixture" / "run_id=run-1" / "payload.bin"
    assert payload.read_bytes() == response.payload
    with pytest.raises(FileExistsError):
        BronzeWriter(tmp_path).persist(response, "run-1")
