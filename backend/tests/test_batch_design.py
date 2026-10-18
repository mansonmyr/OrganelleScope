import pytest
from organelle_scope.batch_design import summarize_design
from organelle_scope.experiments import ExperimentRequest, analyze_experiment
from organelle_scope.image_io import ImageError


def entry(ident, digest, condition='control', experiment='E1', cell='C1'):
    return {'image_id':ident,'image':{'sha256':digest},'condition':condition,'experiment':experiment,'cell':cell}


def test_design_counts_nested_cells_missing_labels_and_repeated_sources():
    rows=[entry('a','same'),entry('b','same',cell='C2'),entry('c','other',experiment='E2'),entry('d','third',condition='',experiment='',cell='')]
    review=summarize_design(rows)
    group=next(g for g in review['groups'] if g['condition']=='control')
    assert group=={'condition':'control','images':3,'labelled_experiments':2,'labelled_cells':3,'images_missing_design_labels':0}
    assert review['groups'][0]['images_missing_design_labels']==1
    assert review['repeated_sources'][0]['image_ids']==['a','b']
    assert not review['repeated_sources'][0]['conflicting_experiments_or_conditions']


@pytest.mark.parametrize('change',[{'experiment':'E2'},{'condition':'treated'}])
def test_identical_raw_data_cannot_count_as_different_experiments_or_conditions(change):
    a=entry('a','same');b=entry('b','same');b.update(change)
    options=ExperimentRequest(run_id='synthetic',conditions=['control','treated'],design='independent_experiments')
    with pytest.raises(ImageError,match='Identical raw source'):
        analyze_experiment({'id':'synthetic','items':[a,b]},options)
