import subprocess
import os
import msprime
from langchain.tools import tool

WORKSPACE_DIR = "./workspace"
SEED_REPO_DIR = "./bio_seeds"

@tool
def simulate_dna_reads_paired(reference_fasta: str, num_reads: int = 1000, mutation_rate: float = 0.001) -> tuple[str, str]:
    print(f"Simulating {num_reads} paired-end DNA reads...")
    r1_path = os.path.join(WORKSPACE_DIR, "sim_reads_r1.fastq")
    r2_path = os.path.join(WORKSPACE_DIR, "sim_reads_r2.fastq")
    cmd = [
        "conda", "run", "-n", "bio_agent_env", "wgsim",
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
        
    print(f"DNA reads generated at: {r1_path}, {r2_path}")
    return r1_path, r2_path

@tool
def align_reads_bwa(reference_fasta: str, reads_r1_fastq: str, reads_r2_fastq: str) -> str:
    print(f"Aligning reads from {reads_r1_fastq} and {reads_r2_fastq} to {reference_fasta}...")
    if not os.path.exists(reference_fasta + ".bwt"):
        print(f"Indexing reference fasta: {reference_fasta}...")
        subprocess.run(["conda", "run", "-n", "bio_agent_env", "bwa", "index", reference_fasta], check=True)

    sam_path = os.path.join(WORKSPACE_DIR, "aligned_reads.sam")
    bam_path = os.path.join(WORKSPACE_DIR, "aligned_reads.bam")
    sorted_bam_path = os.path.join(WORKSPACE_DIR, "aligned_reads.sorted.bam")
    with open(sam_path, "w") as f_sam:
        cmd_bwa = ["conda", "run", "-n", "bio_agent_env", "bwa", "mem", "-t", "4", reference_fasta, reads_r1_fastq, reads_r2_fastq]
        result = subprocess.run(cmd_bwa, stdout=f_sam, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"BWA-MEM failed: {result.stderr}")
    
    subprocess.run(["conda", "run", "-n", "bio_agent_env", "samtools", "view", "-bS", sam_path, "-o", bam_path], check=True)
    subprocess.run(["conda", "run", "-n", "bio_agent_env", "samtools", "sort", bam_path, "-o", sorted_bam_path], check=True)
    subprocess.run(["conda", "run", "-n", "bio_agent_env", "samtools", "index", sorted_bam_path], check=True)
    
    os.remove(sam_path)
    os.remove(bam_path) 

    print(f"Reads aligned. Sorted BAM at: {sorted_bam_path}")
    return sorted_bam_path

@tool
def call_variants_bcftools(sorted_bam: str, reference_fasta: str) -> str:
    print(f"Calling variants from {sorted_bam}...")
    vcf_path = os.path.join(WORKSPACE_DIR, "variants.vcf.gz")
    if not os.path.exists(reference_fasta + ".fai"):
        subprocess.run(["conda", "run", "-n", "bio_agent_env", "samtools", "faidx", reference_fasta], check=True)
    cmd_mpileup = ["conda", "run", "-n", "bio_agent_env", "bcftools", "mpileup", "-f", reference_fasta, sorted_bam]
    cmd_call = ["conda", "run", "-n", "bio_agent_env", "bcftools", "call", "-mv", "-Oz", "-o", vcf_path]

    p1 = subprocess.Popen(cmd_mpileup, stdout=subprocess.PIPE)
    p2 = subprocess.run(cmd_call, stdin=p1.stdout, capture_output=True, text=True)
    p1.stdout.close()
    
    if p2.returncode != 0:
        raise RuntimeError(f"bcftools failed: {p2.stderr}")
    subprocess.run(["conda", "run", "-n", "bio_agent_env","bcftools", "index", vcf_path], check=True)

    print(f"Variants called. VCF file at: {vcf_path}")
    return vcf_path

@tool
def simulate_variants_msprime(sample_size: int = 10, length: int = 10000) -> str:

    print(f"Simulating variants for {sample_size} samples with msprime...")
    vcf_path = os.path.join(WORKSPACE_DIR, "msprime_sim.vcf")

    ts = msprime.sim_ancestry(
        samples=sample_size, 
        population_size=10_000, 
        sequence_length=length, 
        recombination_rate=1e-8,
        random_seed=42
    )
    mts = msprime.sim_mutations(ts, rate=1e-8, random_seed=42)
    with open(vcf_path, "w") as vcf_file:
        mts.write_vcf(vcf_file, contig_id="sim_contig")
    print(f"Variants simulated by msprime at: {vcf_path}")
    return vcf_path
