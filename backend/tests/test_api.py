import io
import json

import numpy as np
import tifffile
from fastapi.testclient import TestClient

from organelle_scope.main import create_app


def test_import_identity_native_plane_auth_and_persistent_metadata(tmp_path):
    app = create_app(tmp_path, "test-session")
    headers = {"X-Session-Token": "test-session"}
    data = np.arange(2 * 3 * 8 * 9, dtype=np.uint16).reshape(2, 3, 8, 9)
    buf = io.BytesIO()
    tifffile.imwrite(buf, data, ome=True, photometric="minisblack", metadata={"axes": "CZYX"})
    with TestClient(app) as client:
        assert client.post("/api/images", files={"file": ("same.tif", buf.getvalue())}).status_code == 401
        records = [client.post("/api/images", headers=headers, files={"file": ("same.tif", buf.getvalue())}).json() for _ in range(2)]
        assert records[0]["id"] != records[1]["id"]
        assert records[0]["sha256"] == records[1]["sha256"]
        image_id = records[0]["id"]
        assert len(client.get("/api/images", headers=headers).json()) == 2
        response = client.get(f"/api/images/{image_id}/plane?z=2&channel=1", headers=headers)
        assert response.status_code == 200
        np.testing.assert_array_equal(np.frombuffer(response.content, "<u2").reshape(8, 9), data[1, 2])
        assert client.get(f"/api/images/{image_id}/plane?z=99", headers=headers).status_code == 422
        assert client.get(f"/api/images/{image_id}/preview?z=1", headers=headers).headers["content-type"] == "image/png"
        patched = client.post(f"/api/images/{image_id}/inspect", headers=headers, json={"spacing_um": {"X": .1, "Y": .2, "Z": .3}})
        assert patched.status_code == 200
    with TestClient(create_app(tmp_path, "new-session")) as client:
        persisted = client.get(f"/api/images/{image_id}", headers={"X-Session-Token": "new-session"}).json()
        assert persisted["info"]["calibration"]["Z"]["value_um"] == .3


def test_bad_upload_is_removed(tmp_path):
    with TestClient(create_app(tmp_path, "token")) as client:
        response = client.post("/api/images", headers={"X-Session-Token": "token"}, files={"file": ("bad.tif", b"invalid")})
        assert response.status_code == 422
        assert list(tmp_path.iterdir()) == []


def test_volume_has_calibrated_geometry_and_requires_scale(tmp_path):
    with TestClient(create_app(tmp_path, "token")) as client:
        headers = {"X-Session-Token": "token"}
        buf = io.BytesIO()
        source = np.arange(3 * 8 * 9, dtype=np.uint16).reshape(3, 8, 9)
        tifffile.imwrite(buf, source, ome=True, photometric="minisblack", metadata={"axes": "ZYX"})
        image_id = client.post("/api/images", headers=headers, files={"file": ("z.tif", buf.getvalue())}).json()["id"]
        assert client.get(f"/api/images/{image_id}/volume", headers=headers).status_code == 422
        client.post(f"/api/images/{image_id}/inspect", headers=headers, json={"spacing_um": {"X": .1, "Y": .2, "Z": .3}})
        response = client.get(f"/api/images/{image_id}/volume", headers=headers)
        assert response.status_code == 200
        assert response.headers["X-Volume-Shape"] == "[3, 8, 9]"
        assert response.headers["X-Volume-Spacing"] == "[0.1, 0.2, 0.3]"
        np.testing.assert_array_equal(np.frombuffer(response.content, "<u2").reshape(source.shape), source)


def test_old_import_records_are_reinspected_without_reusing_implicit_scale(tmp_path):
    headers = {"X-Session-Token": "token"}
    with TestClient(create_app(tmp_path, "token")) as client:
        buf = io.BytesIO()
        tifffile.imwrite(buf, np.zeros((8, 9), np.uint16), resolution=(300, 300), resolutionunit="INCH")
        record = client.post("/api/images", headers=headers, files={"file": ("dpi.tif", buf.getvalue())}).json()
        record.pop("import_schema")
        record["info"]["calibration"]["X"]["value_um"] = 25400/300
        path = tmp_path / record["id"] / "metadata.json"
        path.write_text(json.dumps(record))
        revised = client.get("/api/images", headers=headers).json()[0]
        assert revised["import_schema"] == 2
        assert revised["info"]["calibration"]["X"]["value_um"] is None


def test_uncalibrated_voxel_preview_is_explicit_and_does_not_calibrate_source(tmp_path):
    with TestClient(create_app(tmp_path,'token')) as client:
        h={'X-Session-Token':'token'};buf=io.BytesIO()
        data=np.arange(3*260*9,dtype=np.uint16).reshape(3,260,9)
        tifffile.imwrite(buf,data,ome=True,photometric='minisblack',metadata={'axes':'ZYX'})
        record=client.post('/api/images',headers=h,files={'file':('unknown-scale.tif',buf.getvalue())}).json()
        url=f'/api/images/{record["id"]}'
        assert client.get(url+'/volume',headers=h).status_code==422
        response=client.get(url+'/volume?units=voxel',headers=h)
        assert response.status_code==200
        assert response.headers['X-Volume-Units']=='voxel'
        assert json.loads(response.headers['X-Volume-Spacing'])==[1.,3.,1.]
        np.testing.assert_array_equal(np.frombuffer(response.content,'<u2').reshape(3,87,9),data[:,::3,:])
        assert client.get(url,headers=h).json()['info']['calibration']['X']['value_um'] is None
        assert client.get(url+'/volume?units=wrong',headers=h).status_code==422
