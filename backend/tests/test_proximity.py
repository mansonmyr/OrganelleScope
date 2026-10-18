import io
import numpy as np
import pytest
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.proximity import proximity_summary


def test_exact_z_spacing_direction_denominators_and_inclusive_distance():
    a=np.zeros((3,4,5),bool);b=a.copy()
    a[0,1,1]=a[2,1,1]=True;b[0,1,1]=True
    r=proximity_summary(a,b,[2,.5,.25],4)
    assert r['marker_to_reference']['median_occupied_voxel_center_um']==2
    assert r['reference_to_marker']['median_occupied_voxel_center_um']==0
    assert r['marker_to_reference']['within_distance_voxels']==2
    assert r['reference_to_marker']['source_voxels']==1
    assert r['overlapping_foreground_voxels']==1
    assert proximity_summary(a,b,[2,.5,.25],3.99)['fraction_marker_voxels_within_distance']==.5


def test_empty_masks_are_undefined_and_bad_calibration_rejected():
    a=np.zeros((1,3,3),bool);b=np.ones_like(a)
    assert proximity_summary(a,b,[1,1,1],1)['unavailable_reason']=='Marker mask is empty.'
    assert proximity_summary(b,a,[1,1,1],1)['unavailable_reason']=='Reference mask is empty.'
    for spacing in [[0,1,1],[float('nan'),1,1],[None,1,1]]:
        with pytest.raises(ValueError):proximity_summary(b,b,spacing,1)


def test_reference_search_is_limited_to_cuboid_and_full_z_signal_is_used(tmp_path):
    data=np.zeros((2,4,5,6),np.uint16)
    data[0,1,2,2]=100;data[1,3,2,2]=100;data[1,1,2,0]=100
    stream=io.BytesIO();tifffile.imwrite(stream,data,ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.2,'PhysicalSizeY':.5,'PhysicalSizeZ':2})
    with TestClient(create_app(tmp_path,'t')) as client:
        h={'X-Session-Token':'t'}
        image=client.post('/api/images',headers=h,files={'file':('distances.tif',stream.getvalue())}).json()
        base={'x0':1,'x1':5,'y0':0,'y1':4,'z0':0,'z1':3,'channel':0,'method':'manual','threshold':10,'min_voxels':1,'reference_channel':1,'reference_threshold':10,'near_distance_um':1}
        def measure(**changes):
            response=client.post('/api/images/'+image['id']+'/segmentation',headers=h,json={**base,**changes})
            assert response.status_code==200,response.text
            return response.json()['proximity']
        assert measure()['nearest_occupied_voxel_center_um']==4
        assert measure(x0=0)['nearest_occupied_voxel_center_um']==pytest.approx(.4)
        assert 'Reference mask is empty' in measure(z1=2)['unavailable_reason']


def test_translation_and_unit_scaling_preserve_the_conditional_fraction():
    a=np.zeros((3,4,5),bool);b=a.copy();a[1,1,1]=a[2,2,2]=True;b[0,2,3]=True
    original=proximity_summary(a,b,[2,.5,.25],3)
    translated=proximity_summary(np.pad(a,((1,2),(2,1),(3,0))),np.pad(b,((1,2),(2,1),(3,0))),[2,.5,.25],3)
    scaled=proximity_summary(a,b,[20,5,2.5],30)
    for key in ['marker_to_reference','reference_to_marker']:
        assert original[key]['median_occupied_voxel_center_um']==translated[key]['median_occupied_voxel_center_um']
        assert scaled[key]['median_occupied_voxel_center_um']==pytest.approx(original[key]['median_occupied_voxel_center_um']*10)
        assert scaled[key]['fraction_within_distance']==original[key]['fraction_within_distance']


def test_exhaustive_independent_distance_oracle():
    import runpy
    from pathlib import Path
    suite=runpy.run_path(str(Path(__file__).resolve().parents[2]/'scripts/validation/benchmark_proximity.py'))
    assert len(suite['assess']()['cases'])==60
