"""A fresh profile is empty even when another account has retained research data."""
import io
import numpy as np
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app


def test_fresh_account_is_empty_and_existing_account_retains_work(tmp_path):
    headers = {'X-Session-Token': 'session'}
    existing = tmp_path / 'existing-account' / 'images'
    fresh = tmp_path / 'new-account' / 'images'
    with TestClient(create_app(existing, 'session')) as client:
        stream = io.BytesIO()
        tifffile.imwrite(stream, np.arange(64, dtype=np.uint16).reshape(8, 8), photometric='minisblack')
        response = client.post('/api/images', headers=headers, files={'file': ('retained.tif', stream.getvalue())})
        assert response.status_code == 200
        record = response.json()
        response = client.post('/api/projects', headers=headers, json={
            'name': 'Retained research', 'image_id': record['id'],
            'expected_image_info': record['info'], 'state': {'core': {'z': 0}},
        })
        assert response.status_code == 200
        project_id = response.json()['id']
    with TestClient(create_app(fresh, 'session')) as client:
        for route in ['/api/images', '/api/projects']:
            response = client.get(route, headers=headers)
            assert response.status_code == 200 and response.json() == []
        assert client.get('/api/recovery', headers=headers).json() is None
    with TestClient(create_app(existing, 'session')) as client:
        assert client.get('/api/images', headers=headers).json()[0]['id'] == record['id']
        assert client.get('/api/projects', headers=headers).json()[0]['id'] == project_id
