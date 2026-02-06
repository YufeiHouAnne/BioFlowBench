import os
import pandas as pd
import numpy as np
from langchain.tools import tool

WORKSPACE_DIR = "/home/houyufei/yfhou/biotoolbenchmark/BioGen_Data/workspace"

@tool
def simulate_metabolomics_peak_list(
    num_compounds: int = 100,
    num_samples: int = 20,
    noise_level: float = 0.1
) -> str:
    """
    使用 Numpy 和 Pandas 模拟一个代谢组学的峰列表。
    生成一个 CSV 文件，其中包含每个样本中每个化合物的 m/z、保留时间和强度。
    返回生成的 CSV 文件路径。
    """
    print(f"🧬 Simulating metabolomics peak list...")
    csv_path = os.path.join(WORKSPACE_DIR, "simulated_metabolomics_peaks.csv")
    
    # 1. 生成化合物的基本信息 (m/z 和 RT)
    compounds = pd.DataFrame({
        'mz': np.random.uniform(100, 1000, num_compounds),
        'rt': np.random.uniform(1, 20, num_compounds)
    })
    
    # 2. 为每个样本生成强度值
    sample_names = [f'sample_{i+1}' for i in range(num_samples)]
    intensities = pd.DataFrame(index=compounds.index, columns=sample_names)
    
    # 模拟一些化合物在样本组之间有差异
    half_samples = num_samples // 2
    for i in range(num_compounds):
        if i < num_compounds / 4: # 1/4的化合物在第一组高表达
            group1_intensity = np.random.lognormal(mean=10, sigma=1, size=half_samples)
            group2_intensity = np.random.lognormal(mean=8, sigma=1, size=num_samples - half_samples)
            intensities.iloc[i] = np.concatenate([group1_intensity, group2_intensity])
        elif i < num_compounds / 2: # 1/4的化合物在第二组高表达
            group1_intensity = np.random.lognormal(mean=8, sigma=1, size=half_samples)
            group2_intensity = np.random.lognormal(mean=10, sigma=1, size=num_samples - half_samples)
            intensities.iloc[i] = np.concatenate([group1_intensity, group2_intensity])
        else: # 一半的化合物无差异
            base_intensity = np.random.lognormal(mean=9, sigma=1.5, size=num_samples)
            intensities.iloc[i] = base_intensity

    # 3. 添加噪声峰
    num_noise_peaks = int(num_compounds * noise_level)
    noise_mz = np.random.uniform(100, 1000, num_noise_peaks)
    noise_rt = np.random.uniform(1, 20, num_noise_peaks)
    noise_intensities = np.random.lognormal(mean=5, sigma=1, size=(num_noise_peaks, num_samples))
    
    noise_df = pd.DataFrame(noise_intensities, columns=sample_names)
    noise_df['mz'] = noise_mz
    noise_df['rt'] = noise_rt

    # 4. 合并数据并保存
    final_df = pd.concat([compounds, intensities], axis=1)
    final_df = pd.concat([final_df, noise_df], ignore_index=True)
    
    final_df.to_csv(csv_path, index=False)

    print(f"✅ Metabolomics peak list CSV generated at: {csv_path}")
    return csv_path