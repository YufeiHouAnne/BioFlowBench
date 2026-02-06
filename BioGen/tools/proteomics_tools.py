import os
from langchain.tools import tool
import pyopenms
from pyopenms import ProteaseDB, ResidueDB, FASTAFile, ProteaseDigestion, AASequence
from pyopenms import *
import os
WORKSPACE_DIR = "/home/houyufei/yfhou/biotoolbenchmark/BioGen_Data/workspace"
SEED_REPO_DIR = "/home/houyufei/yfhou/biotoolbenchmark/BioGen_Data/bio_seeds"

from pyopenms import *
import os

@tool
def simulate_ms_spectra_pyopenms(
    protein_fasta: str,
    enzyme: str = "Trypsin"
) -> str:
    """
    使用 pyOpenMS 从蛋白质 FASTA 文件模拟质谱实验（LC-MS/MS）。
    这个过程包括：蛋白质酶切、肽段标记、质谱模拟。
    返回生成的 mzML 文件路径。
    """
    print(f"🧬 Simulating proteomics MS/MS spectra with pyOpenMS...")
    mzml_path = os.path.join(WORKSPACE_DIR, "simulated_proteomics.mzML")
    
    # 1. 加载蛋白质序列
    proteins = []
    ff = FASTAFile()
    ff.load(protein_fasta, proteins)

    # 2. 酶切
    dig = ProteaseDigestion()
    dig.setEnzyme(enzyme)
    peptides = []
    print("  - Digesting proteins...")
    for protein in proteins:
        result = []
        # 将字符串转为 AASequence 对象
        protein_seq = AASequence.fromString(protein.sequence)
        dig.digest(protein_seq, result)
        peptides.extend(result)
    
    # 去重
    # 注意：为了后续处理方便，这里先转为字符串去重
    unique_peptide_seqs = list(set([p.toString() for p in peptides if 6 <= p.size() <= 40]))
    print(f"  - Digested into {len(unique_peptide_seqs)} unique peptides.")

    # ⚠️ 限制数量：只模拟前 100 个肽段，防止内存溢出和耗时过长
    subset_size = 100
    target_peptides = unique_peptide_seqs[:subset_size]
    print(f"  - Simulating spectra for top {subset_size} peptides...")

    # 3. 使用 TheoreticalSpectrumGenerator 生成谱图
    tsg = TheoreticalSpectrumGenerator()
    
    # 设置模拟参数 (移除不支持的 noise 参数)
    spec_params = tsg.getParameters()
    spec_params.setValue("add_b_ions", "true")
    spec_params.setValue("add_y_ions", "true")
    spec_params.setValue("add_losses", "true") # 添加中性丢失
    tsg.setParameters(spec_params)

    exp = MSExperiment()
    
    for i, pep_str in enumerate(target_peptides):
        # 创建一个空谱图
        spec = MSSpectrum()
        
        # 将字符串转回 AASequence
        peptide = AASequence.fromString(pep_str)
        
        # 生成理论谱图 (电荷 1 到 2)
        # getSpectrum(spectrum, peptide, min_charge, max_charge)
        tsg.getSpectrum(spec, peptide, 1, 2)
        
        # 设置模拟的保留时间 (RT) 和 ID
        spec.setRT(i * 2.0)
        spec.setNativeID(f"spectrum_{i}")
        
        # 将谱图加入实验
        exp.addSpectrum(spec)

    # 4. 存储
    # 移除了 exp.setDocIdentifier，因为它导致报错且不是必须的
    
    # 存储文件
    MzMLFile().store(mzml_path, exp)
    
    print(f"✅ Proteomics mzML file simulated by pyOpenMS at: {mzml_path}")
    return mzml_path