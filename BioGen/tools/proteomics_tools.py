import os
from langchain.tools import tool
import pyopenms
from pyopenms import ProteaseDB, ResidueDB, FASTAFile, ProteaseDigestion, AASequence
from pyopenms import *
import os
WORKSPACE_DIR = "./workspace"
SEED_REPO_DIR = "./bio_seeds"

from pyopenms import *
import os

@tool
def simulate_ms_spectra_pyopenms(
    protein_fasta: str,
    enzyme: str = "Trypsin"
) -> str:
    print(f"🧬 Simulating proteomics MS/MS spectra with pyOpenMS...")
    mzml_path = os.path.join(WORKSPACE_DIR, "simulated_proteomics.mzML")
    proteins = []
    ff = FASTAFile()
    ff.load(protein_fasta, proteins)
    dig = ProteaseDigestion()
    dig.setEnzyme(enzyme)
    peptides = []
    print("  - Digesting proteins...")
    for protein in proteins:
        result = []
        protein_seq = AASequence.fromString(protein.sequence)
        dig.digest(protein_seq, result)
        peptides.extend(result)
    
    unique_peptide_seqs =list(set([p.toString() for p in peptides if 6 <= p.size() <= 40]))
    print(f"  - Digested into {len(unique_peptide_seqs)} unique peptides.")
    subset_size = 100
    target_peptides = unique_peptide_seqs[:subset_size]
    print(f"  - Simulating spectra for top {subset_size} peptides...")
    tsg = TheoreticalSpectrumGenerator()

    spec_params = tsg.getParameters()
    spec_params.setValue("add_b_ions", "true")
    spec_params.setValue("add_y_ions", "true")
    spec_params.setValue("add_losses", "true") 
    tsg.setParameters(spec_params)

    exp = MSExperiment()
    
    for i, pep_str in enumerate(target_peptides):
        spec = MSSpectrum()
        peptide = AASequence.fromString(pep_str)
        tsg.getSpectrum(spec, peptide, 1, 2)
        spec.setRT(i * 2.0)
        spec.setNativeID(f"spectrum_{i}")
        exp.addSpectrum(spec)
    MzMLFile().store(mzml_path, exp)
    
    print(f"✅ Proteomics mzML file simulated by pyOpenMS at: {mzml_path}")
    return mzml_path
