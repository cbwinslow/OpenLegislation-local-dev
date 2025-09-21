# NVIDIA GPU Setup Guide for GovInfo Data Processing

This guide covers setting up NVIDIA K80 and K40 GPUs on Ubuntu servers for accelerating congress.gov data ingestion and processing.

## Hardware Requirements

- **NVIDIA K80 GPU**: Tesla K80 (dual GK210 GPUs, 24GB GDDR5 per GPU, 4992 CUDA cores total)
- **NVIDIA K40 GPU**: Tesla K40 (single GK110 GPU, 12GB GDDR5, 2880 CUDA cores)
- **Ubuntu Server**: 20.04 LTS or 22.04 LTS recommended
- **Power Supply**: K80 requires 300W, K40 requires 235W
- **PCIe**: PCIe 3.0 x16 slot required

## Installation Steps

### 1. Update System and Install Prerequisites

```bash
# Update package lists
sudo apt update
sudo apt upgrade -y

# Install build tools and prerequisites
sudo apt install -y build-essential gcc make linux-headers-$(uname -r)
sudo apt install -y pkg-config libglvnd-dev
```

### 2. Install NVIDIA Drivers

#### Option A: Ubuntu Graphics Drivers PPA (Recommended)

```bash
# Add graphics drivers PPA
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update

# Install NVIDIA driver (470 series for K80/K40 compatibility)
sudo apt install -y nvidia-driver-470

# Reboot system
sudo reboot
```

#### Option B: NVIDIA CUDA Repository

```bash
# Download CUDA keyring
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb

# Update and install CUDA (includes drivers)
sudo apt update
sudo apt install -y cuda-drivers-470

# Reboot system
sudo reboot
```

### 3. Verify GPU Installation

```bash
# Check NVIDIA driver
nvidia-smi

# Expected output should show your K80/K40 GPU(s)
# For K80: Should show two GPU devices
# For K40: Should show one GPU device

# Check CUDA version
nvcc --version
```

### 4. Install CUDA Toolkit

```bash
# Install CUDA 11.4 (compatible with K80/K40)
sudo apt install -y cuda-11-4

# Add CUDA to PATH
echo 'export PATH=/usr/local/cuda-11.4/bin${PATH:+:${PATH}}' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.4/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> ~/.bashrc
source ~/.bashrc
```

### 5. Install cuDNN (for deep learning acceleration)

```bash
# Download cuDNN from NVIDIA website (requires account)
# https://developer.nvidia.com/cudnn

# Install cuDNN
sudo dpkg -i libcudnn8_8.2.4.15-1+cuda11.4_amd64.deb
sudo dpkg -i libcudnn8-dev_8.2.4.15-1+cuda11.4_amd64.deb
```

## Python GPU Libraries

### Install PyTorch with CUDA support

```bash
# Install PyTorch for CUDA 11.4
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu114
```

### Install TensorFlow with GPU support

```bash
# Install TensorFlow GPU
pip install tensorflow-gpu==2.8.0
```

### Install RAPIDS (for data processing acceleration)

```bash
# Install RAPIDS (GPU-accelerated pandas-like operations)
# Note: May require specific CUDA version compatibility
pip install cudf cuml
```

## GPU-Accelerated Data Processing

### Text Processing with GPU

For bill text processing, you can use GPU acceleration for:

1. **Text tokenization and preprocessing**
2. **Named entity recognition**
3. **Document similarity calculations**
4. **Text classification and categorization**

#### Example: GPU-accelerated text processing

```python
import torch
import transformers
from transformers import AutoTokenizer, AutoModel

# Check GPU availability
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Load BERT model for text processing
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
model = AutoModel.from_pretrained('bert-base-uncased').to(device)

def process_bill_text_gpu(text):
    """Process bill text using GPU acceleration"""
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.cpu().numpy()
```

### Database Operations with GPU

For large-scale data processing:

```python
import cudf
import pandas as pd

# Load data with GPU acceleration
def load_bill_data_gpu(file_path):
    """Load bill data using GPU-accelerated pandas"""
    df = cudf.read_csv(file_path)  # or read_json, read_parquet, etc.

    # Perform GPU-accelerated operations
    df['text_length'] = df['bill_text'].str.len()
    df['processed_text'] = df['bill_text'].str.lower()

    return df.to_pandas()  # Convert back to pandas if needed
```

## Performance Optimization

### Memory Management

```python
# Clear GPU memory
torch.cuda.empty_cache()

# Monitor GPU memory usage
print(f"GPU memory allocated: {torch.cuda.memory_allocated()/1024**2:.2f} MB")
print(f"GPU memory cached: {torch.cuda.memory_reserved()/1024**2:.2f} MB")
```

### Multi-GPU Setup (K80)

The K80 has two GPUs - you can use both:

```python
# Use specific GPU
torch.cuda.set_device(0)  # or 1 for second GPU

# Data parallelism
if torch.cuda.device_count() > 1:
    model = torch.nn.DataParallel(model)
```

## Monitoring and Troubleshooting

### GPU Monitoring

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# GPU utilization over time
nvidia-smi --query-gpu=timestamp,utilization.gpu,utilization.memory --format=csv -l 1
```

### Common Issues

1. **Driver conflicts**: Remove old drivers before installing new ones
   ```bash
   sudo apt purge nvidia*
   sudo apt autoremove
   ```

2. **CUDA version mismatch**: Ensure CUDA toolkit matches driver version
   - Driver 470 supports CUDA 11.4

3. **Memory issues**: Monitor GPU memory usage and clear cache when needed

4. **Power/thermal throttling**: Ensure adequate cooling and power supply

## Integration with GovInfo Processing

### Modify govinfo_data_connector.py for GPU support

```python
import torch

class GPUAcceleratedGovInfoConnector(GovInfoDataConnector):
    def __init__(self, db_config, use_gpu=True):
        super().__init__(db_config)
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device('cuda' if self.use_gpu else 'cpu')

    def process_text_gpu(self, text):
        """GPU-accelerated text processing"""
        if not self.use_gpu:
            return text

        # Implement GPU text processing here
        # Tokenization, embedding, etc.
        return processed_text
```

### Environment Variables for GPU Processing

```bash
# Set CUDA visible devices
export CUDA_VISIBLE_DEVICES=0,1  # For K80 dual GPUs

# Enable GPU processing in scripts
export USE_GPU=true
```

## Production Deployment

### Systemd Service for GPU Monitoring

```bash
# Create GPU monitoring service
sudo tee /etc/systemd/system/gpu-monitor.service > /dev/null <<EOF
[Unit]
Description=GPU Monitoring Service

[Service]
ExecStart=/usr/bin/nvidia-smi --query-gpu=timestamp,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.free --format=csv -l 60
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable gpu-monitor
sudo systemctl start gpu-monitor
```

### Automated GPU Health Checks

```bash
#!/bin/bash
# GPU health check script

# Check if GPUs are accessible
nvidia-smi --list-gpus

# Test CUDA functionality
cuda_check=$(python3 -c "import torch; print(torch.cuda.is_available())")
if [ "$cuda_check" != "True" ]; then
    echo "CUDA not available - sending alert"
    # Send alert/notification
fi
```

This setup will enable GPU acceleration for processing the large volumes of congressional data, significantly improving performance for text analysis, data transformation, and machine learning tasks on your homelab server.