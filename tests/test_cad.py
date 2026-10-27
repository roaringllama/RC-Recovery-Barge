import os

import pytest

cq = pytest.importorskip('cadquery')

import design as D
from model import hydro
from tools import cad


@pytest.fixture(scope='module')
def r():
    return hydro.design()


def test_hull_solid_volume_matches_the_sponson_estimate(r):
    vol, est = cad.hull_volume_check(r['deck'])
    # the estimate is plan area times deck height with square bilges; the bilge rounds take about 2 percent off
    assert abs(vol - est) / est < 0.05


def test_hull_solid_is_valid_and_has_two_sponsons(r):
    s = cad._shape(cad.hull_solid(r['deck']))
    assert s.isValid()
    assert len(s.Solids()) == 2
    bb = s.BoundingBox()
    assert abs((bb.xmax - bb.xmin) - D.LOA) < 1.0
    assert abs((bb.ymax - bb.ymin) - D.BEAM) < 1e-6


def test_export_writes_step_glb_and_manifest(tmp_path):
    files, manifest = cad.export_all(str(tmp_path), log=lambda *a: None)
    assert os.path.getsize(files['step']) > 0 and files['step'].endswith('RC_Recovery_Barge_%s.step' % D.REV)
    assert os.path.getsize(files['glb']) > 0 and files['glb'].endswith('RC_Recovery_Barge_%s.glb' % D.REV)
    assert os.path.getsize(files['render_info']) > 0
    for g in ('hull', 'deck', 'caps', 'skegs_shoes', 'nozzles_props', 'blades', 'blades_stowed', 'push_pad', 'electronics', 'water'):
        assert g in manifest['groups'] and manifest['groups'][g]['volume_cm3'] > 0
        assert os.path.exists(os.path.join(str(tmp_path), manifest['groups'][g]['stl']))
