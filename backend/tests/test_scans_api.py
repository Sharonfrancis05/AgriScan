import io

from tests.conftest import make_non_leaf_jpeg, make_synthetic_leaf_jpeg


def test_health_endpoint_reports_model_loaded(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_submit_scan_end_to_end(client):
    image_bytes = make_synthetic_leaf_jpeg(patch_fraction=0.2)

    response = client.post(
        "/api/scans",
        files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["crop_name"] == "Tomato"
    assert body["disease_code"] == "Tomato___late_blight"
    assert body["disease_display_name"] == "Late Blight"
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["infected_area_pct"] >= 0.0
    assert body["severity"] in ("Healthy", "Mild", "Moderate", "Severe", "Critical")
    assert body["report_id"].startswith("AGV-")
    assert body["original_image_url"].startswith("/static/uploads/")
    assert body["overlay_image_url"].startswith("/static/uploads/")
    assert body["recommendations"]["treatment"]
    # A clear, coherent synthetic leaf should not trip the reliability gate.
    assert body["prediction_warning"] is None


def test_submit_scan_flags_a_non_leaf_image(client):
    image_bytes = make_non_leaf_jpeg()

    response = client.post(
        "/api/scans",
        files={"image": ("not-a-leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    # The classifier still forces a guess (it's a closed-set softmax model —
    # see app/ml/leaf_validity.py), but the leaf-coverage gate must catch that
    # the image plainly isn't a photographed leaf and surface a warning
    # instead of presenting a confident-looking diagnosis.
    assert body["prediction_warning"] is not None
    assert "no clear leaf detected" in body["prediction_warning"].lower()


def test_submit_scan_rejects_unsupported_content_type(client):
    response = client.post(
        "/api/scans",
        files={"image": ("leaf.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 415


def test_scan_history_and_detail_round_trip(client):
    image_bytes = make_synthetic_leaf_jpeg()
    submit_response = client.post(
        "/api/scans",
        files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    scan_uuid = submit_response.json()["scan_uuid"]

    history_response = client.get("/api/scans")
    assert history_response.status_code == 200
    history_body = history_response.json()
    assert history_body["total"] >= 1
    assert any(item["scan_uuid"] == scan_uuid for item in history_body["items"])

    detail_response = client.get(f"/api/scans/{scan_uuid}")
    assert detail_response.status_code == 200
    assert detail_response.json()["scan_uuid"] == scan_uuid

    missing_response = client.get("/api/scans/does-not-exist")
    assert missing_response.status_code == 404


def test_report_download_returns_a_pdf(client):
    image_bytes = make_synthetic_leaf_jpeg()
    submit_response = client.post(
        "/api/scans",
        files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    report_id = submit_response.json()["report_id"]

    download_response = client.get(f"/api/reports/{report_id}/download")

    assert download_response.status_code == 200
    assert download_response.content[:4] == b"%PDF"
    assert download_response.headers["content-type"] == "application/pdf"


def test_dashboard_stats_reflect_submitted_scans(client):
    image_bytes = make_synthetic_leaf_jpeg()
    client.post("/api/scans", files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")})

    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_scans"] >= 1
    assert isinstance(body["severity_breakdown"], list)
    assert isinstance(body["crop_breakdown"], list)
