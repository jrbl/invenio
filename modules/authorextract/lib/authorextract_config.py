## Lines holding key matches will be replaced with the value at extraction time
CFG_REFEXTRACT_INSTITUTION_REPLACEMENTS = {
    r'^Livermore' : 'LLNL, Livermore',
    r'.*?Stanford Linear Accelerator Center.*?' : 'SLAC',
    r'^Fermi National Accelerator Laboratory' : 'Fermilab'
}

## Lines holding these institutions will be reduced solely to the institution at extraction time
CFG_REFEXTRACT_INSTITUTION_REDUCTIONS = [
    'CERN',
    'DESY',
    'Rutherford',
    'Fermilab',
    'SLAC',
    'TRIUMF',
    'Brookhaven Livermore',
    'Argonne'
]

## The allowable distance between consecutively numerated affiliations
## A small distance value could limit the number of numerated affiliations obtained (default: 2)
CFG_REFEXTRACT_AFFILIATION_NUMERATION_ALLOWABLE_GAP = 2

## refextract author-extraction fields:
CFG_REFEXTRACT_AE_TAG_ID_HEAD_AUTHOR     = "100" ## first author-aff details
CFG_REFEXTRACT_AE_TAG_ID_TAIL_AUTHOR     = "700" ## remaining author-affs
CFG_REFEXTRACT_AE_SUBFIELD_AUTHOR        = "a"   ## authors subfield
CFG_REFEXTRACT_AE_SUBFIELD_AFFILIATION   = "u"   ## affiliations subfield


CFG_REFEXTRACT_MARKER_CLOSING_AFFILIATION= r"</cds.AFF>"
