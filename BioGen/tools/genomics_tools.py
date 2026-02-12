import subprocess
import os
from langchain.tools import tool

WORKSPACE_DIR = "./workspace"
SEED_REPO_DIR = "./bio_seeds"

@tool
def get_seed_file_path(filepath: str) -> str:
    """
    Returns the full path to a file in the seed repository.
    Use this to get paths for reference genomes, annotations, etc.
    """
    print(f"start get_seed_file_path: {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Seed file '{filepath}' not found in '{SEED_REPO_DIR}'.")
    return filepath

@tool
def simulate_dna_reads_paired(reference_fasta: str, num_reads: int = 1000, mutation_rate: float = 0.001) -> tuple[str, str]:
    """
    Simulates paired-end DNA reads from a reference FASTA file using wgsim.
    Returns the paths to the two generated FASTQ files.
    """
    print(f"🧬 Simulating {num_reads} paired-end DNA reads...")
    r1_path = os.path.join(WORKSPACE_DIR, "sim_reads_r1.fastq")
    r2_path = os.path.join(WORKSPACE_DIR, "sim_reads_r2.fastq")
    
    # wgsim command: wgsim -N <num_reads> -r <mut_rate> <ref.fa> <out1.fq> <out2.fq>
    cmd = ["conda", "run", "-n", "bio_agent_env",
        "wgsim",
        "-N", str(num_reads),
        "-r", str(mutation_rate),
        "-d", "300", # outer distance
        "-1", "100", # read length 1
        "-2", "100", # read length 2
        reference_fasta,
        r1_path,
        r2_path,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"wgsim failed: {result.stderr}")
        
    print(f"✅ DNA reads generated at: {r1_path}, {r2_path}")
    return r1_path, r2_path
