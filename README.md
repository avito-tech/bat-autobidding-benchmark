# BAT: Benchmark for Auto-bidding Task

## Overview

This repository contains the benchmark implementation and supplementary materials for our paper "BAT: Benchmark for Auto-bidding Task
" (paper on [OpenReview](https://openreview.net/forum?id=9eRgajXN2w#discussion)). It provides a comprehensive framework for evaluating and comparing different bidding strategies in online advertising auctions.

## Key Features

- Implementation of the following bidding strategies:
  1. ALM
  2. TA-PID
  3. [M-PID](https://arxiv.org/pdf/1905.10928)
  4. [Mystique](https://www.yahooinc.com/research/publications/mystique-a-budget-pacing-system-for-performance-optimization-in-online-advertising)
  5. [BROI](https://arxiv.org/pdf/2301.13306)
- Simulation environment for ad auctions of two types: FPA (First-Price Auction) and VCG (Vickrey–Clarke–Groves) auction
- Data analysis and visualization tools
- Benchmark datasets

## Repository Structure

```
.
├── 📜 LICENSE
├── 📘 README.md
├── 📊 data/                          # Data for VCG and FPA (to be downloaded with dvc)
│   ├── fpa/
│   ├── vcg/
├── 📓 example_notebooks/             # Notebooks with model running examples
│   ├── baseline_bidders.ipynb        # Guideline: how to make experiments with bidders
│   ├── bidder_example.ipynb          # Guideline: how to create new bidder class
│   └── 📊 best_params/
├── 📋 requirements.txt
├── 🛠️ simulator/                      # Main simulator code
│   ├── 💰 model/                      # Bidder models
│   │   ├── bidder.py                  # Parent class for all bidders
│   │   ├── broi_bidder.py           
│   │   ├── linear_bidder.py           # ALM bidder implementation
│   │   ├── m_pid.py                
│   │   ├── mystique.py               
│   │   ├── ta_pid.py
│   │   └── traffic.py
│   ├── 🔄 simulation/                 # Modules for running simulations
│   │   ├── modules.py
│   │   ├── simulate.py
│   │   ├── utils.py
│   │   └── utils_visualization.py
│   └── ✅ validation/                 # Running experiments on all campaigns
│       ├── check_results.py
│       └── metrics.py
└── 📔 useful_notebooks/              # Notebooks with data filtering examples
    ├── filter-fpa.ipynb
    └── filter-vcg.ipynb
```

### Installation

1. Clone the repository: `git clone https://github.com/avito/your-repo-name.git`
2. Install the required packages: `pip install -r requirements.txt`
3. Download data: `dvc pull`

### Experiment Results

The Sum Click Ratio (SCR) for the proposed models:

| Model      | SCR<sup>VCG</sup> | SCR<sup>FP</sup> |
|------------|-------------------|------------------|
| ALM        | 662,466           | 1,085,836        |
| TA-PID     | 909,282           | 1,478,538        |
| M-PID      | 889,251           | 1,240,244        |
| Mystique   | 932,152           | 1,073,291        |
| BROI       | 495,169           | 1,098,184        |

## Contributing

We welcome contributions to improve the benchmark. Please feel free to submit issues or pull requests.

## Citation

If you use this benchmark in your research, please cite our paper: 

```
@inproceedings{khirianova2025bat,
  title={BAT: Benchmark for Auto-bidding Task},
  author={Khirianova, Alexandra and Solodneva, Ekaterina and Pudovikov, Andrey and Osokin, Sergey and Samosvat, Egor and Dorn, Yuriy and Ledovsky, Alexander and Zenkova, Yana},
  booktitle={Proceedings of the ACM on Web Conference 2025},
  pages={2657--2667},
  year={2025}
}
```

## License

This project is licensed under MIT License. See the LICENSE file for details. 

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.14795981.svg)](http://dx.doi.org/10.5281/zenodo.14795981)

