# BAT: Benchmark for Auto-bidding Task
## Overview

This repository contains the benchmark implementation and supplementary materials for our paper "Title" (link). It provides a comprehensive framework for evaluating and comparing different bidding strategies in online advertising auctions.

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
📁 Project Root
├── 📊 data/
│   └── fpa
│   └── vcg
│   └── traffic_share.csv
├── 📓 notebooks/
│   ├── baseline_bidders.ipynb
│   ├── bidder_example.ipynb
│   ├── pictures_rebuttal.ipynb
│   ├── filter-fpa.ipynb
│   └── filter-vcg.ipynb
├── 🛠️ src/
│   ├── 💰 bidders/
│   │   ├── bidder.py
│   │   ├── broi_bidder.py
│   │   ├── linear_bidder.py
│   │   ├── m_pid.py
│   │   ├── mystique.py
│   │   └── ta_pid.py
│   ├── 🔄 simulation/
│   │   ├── modules.py
│   │   ├── simulate.py
│   │   └── traffic.py
│   └── 🔧 utils/
│       ├── check_results.py
│       ├── metrics.py
│       ├── utils.py
│       └── utils_visualization.py
├── 📄 .flake8
├── 📄 .gitattributes
├── 📄 .gitignore
├── 📜 LICENSE
├── 📘 README.md
├── 📋 requirements.txt
```

### Installation

1. Clone the repository: git clone https://github.com/avito/your-repo-name.git
2. Install the required packages: pip install -r requirements.txt
3. Download data: TODO

## Contributing

We welcome contributions to improve the benchmark. Please feel free to submit issues or pull requests.

## Citation

If you use this benchmark in your research, please cite our paper:

## License

This project is licensed under [Your chosen license]. See the LICENSE file for details. 

## Contact

For any questions or feedback, please contact [Solodneva Ekaterina] at [easolodneva@avito.ru].  ????
