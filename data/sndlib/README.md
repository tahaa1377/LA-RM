# Measured traffic: SNDlib Abilene and GEANT

The REPETITA matrices in `data/raw/` are synthetic (a randomized gravity model).
For two backbones we also use **measured** traffic matrices, distributed by SNDlib
together with the topologies they were measured on.

| network | PoPs | links | matrices | interval | period | measured by |
|---|---|---|---|---|---|---|
| `abilene` | 12 | 15 | 48,096 | 5 min | 1 Mar - 10 Sep 2004 | Yin Zhang, from sampled flow measurements of the Abilene backbone |
| `geant` | 22 | 36 | 11,460 (688 empty) | 15 min | 4 May - 31 Aug 2005 | Uhlig et al., GEANT |

Values are in Mbit/s. In the simulator they set only the *relative* demand of each
origin-destination pair (see below); the benign flow rate is calibrated as for the
other backbones.

## Files

| file | content |
|---|---|
| `abilene.topo`, `geant.topo` | SNDlib nodes and undirected links. The simulator routes on unit link weights (hop count), as REPETITA does for most of its graphs |
| `abilene_snapshots.json`, `geant_snapshots.json` | the matrices the experiments use: for ten weekdays, the mean matrix of the busiest and of the quietest full clock hour (UTC) |
| `raw/` (not shipped) | the full series; see below |

`experiments/prepare_sndlib.py` rebuilds the snapshot files from the full series.

## How the matrices are chosen

- **Days.** Weekdays on which at least 90% of the intervals hold a non-empty matrix and
  no interval carries more than 10 times the day's median total, ten of them evenly
  spaced over the series. The 10x rule removes one GEANT day, 27 June 2005, whose
  totals reach 36 times the day's median. That is an artefact, not traffic.
- **Hours.** On each day, the busy hour and the quiet hour are the full clock hours with
  the largest and the smallest total traffic. The matrix of an hour is the mean of its
  12 (Abilene) or 4 (GEANT) measured matrices.
- **Runs.** A run (110 s) is shorter than one measurement interval, so a run uses one
  matrix throughout. Seed *k* uses day *k*, so every policy sees the same matrix for a
  seed.
- **Load.** Every busy hour gets the same benign flow rate, so days differ only in where
  the traffic goes. A quiet hour (`LARM_HOUR=quiet`) gets the fraction of its day's
  busy-hour total that was measured.

## Sources and checks

- **SNDlib** (dynamic traffic section): https://sndlib.put.poznan.pl (formerly
  http://sndlib.zib.de). The Abilene series is the archive
  `directed-abilene-zhang-5min-over-6months-ALL`, one XML file per matrix
  (`demandMatrix-abilene-zhang-5min-YYYYMMDD-HHMM.xml`). Their metadata names Yin Zhang's
  AbileneTM page as the origin.
- **Mirror used here.** We could not download the series from the SNDlib server, so we
  read it from a CSV conversion on GitHub:
  - repository `lasseufpa/Unsupervised-Concept-Drift-Detection`, commit
    `b1c9d2db9b927507f999c870af33b6c37f6ff6d0`
  - files `datasets/abilene_demand_matrix.csv` (SHA-256
    `a7ad071d61465cd46a432486c9ed37c9dbb5ce18150285055519fed3b6a31245`) and
    `datasets/geant_demand_matrix.csv` (SHA-256
    `9dd0ffb2fc665e938194420cd8496a3c98ddf2b59c9095e3b8da478285bfc62d`)
- **Check against the original Abilene files.** Ten original SNDlib Abilene XML matrices,
  taken from a second, independent copy, were compared with the CSV and are identical,
  with a largest difference of 0 Mbit/s. The second copy is
  `RealVNF/coord-sim`, `params/convert_traces/directed-abilene-zhang-5min-over-6months-ALL/`,
  and the check is
  `prepare_sndlib.py abilene <csv> --verify-xml <folder>`.
- **GEANT.** We had no original GEANT XML file to compare against. Before publishing,
  run the same check with the official archive.
- **Topologies.** These come from SNDlib's native network files, as packaged in the
  `topohub` 1.5.1 package on PyPI. They match SNDlib's published sizes (12/15 and 22/36).

SNDlib states no redistribution licence, so this repository ships only the derived
hourly snapshots, not the full series. To rebuild them, download the series from SNDlib
or from the mirror above into `raw/`, then run:

```
python experiments/prepare_sndlib.py abilene data/sndlib/raw/abilene_demand_matrix.csv.gz
python experiments/prepare_sndlib.py geant   data/sndlib/raw/geant_demand_matrix.csv.gz
```

`prepare_sndlib.py` also accepts a folder of SNDlib XML files in place of the CSV.

## Citing

- S. Orlowski, R. Wessäly, M. Pióro, and A. Tomaszewski, "SNDlib 1.0—Survivable network
  design library," *Networks*, vol. 55, no. 3, pp. 276–286, 2010.
- S. Uhlig, B. Quoitin, J. Lepropre, and S. Balon, "Providing public intradomain traffic
  matrices to the research community," *ACM SIGCOMM Comput. Commun. Rev.*, vol. 36,
  no. 1, pp. 83–86, 2006.
- Abilene: Y. Zhang, "Abilene traffic matrices,"
  https://www.cs.utexas.edu/~yzhang/research/AbileneTM/ (the origin named in the SNDlib
  files).
