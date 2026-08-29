# NanoSpecies-50

Artifact for **"NanoSpecies-50: A Reproducible Cross-Species Benchmark for
Nanopore Basecalling and an Audited Pure-PyTorch CRF Decoder"** (IEEE BIBM
submission).

NanoSpecies-50 is a read-level benchmark over 50 bacterial isolates spanning 13
genera, built around a fully deterministic protocol: a fixed manifest selects the
same 100 reads per isolate (5,000 evaluation reads in total), references are
assembly-anchored per read, and
decoding uses an audited **pure-PyTorch CTC-CRF Viterbi decoder** shipped here in
place of the vendor's closed-source CUDA kernel. Because the protocol uses no
random seeds and no vendor CUDA decoder, every number in the paper is a
deterministic function of the checkpoint and corpus, and the whole evaluation
runs unchanged on CPU, CUDA, and ARM-based GH200.

## Layout

```
koi/                    audited pure-PyTorch CTC-CRF decoder (drop-in for ONT's closed-source koi)
  ctc.py                Viterbi decoding + forward-backward in the Log/Max semirings, no CUDA kernels
  decode.py, lstm.py    remaining import surface Bonito expects
scripts/phase2/
  eval_bonito_basecaller.py      vendor-checkpoint evaluation (Algorithm 1)
  load_dorado_crf.py             loads legacy Dorado checkpoints (works on ARM, where vendor binaries do not)
  patch_dorado_multi.py          multi-checkpoint Dorado loading
  eval_8iso.py                   8-isolate smoke subset
  eval_dorado_sup_all.sh         Dorado sup over all isolates
  eval_bonito_hac_all.sh         Bonito hac over all isolates
  eval_nanospecies50.sh          full NS-50 sweep for the student models
  eval_student_nanospecies50.py  python core of the student evaluation
  eval_ablation50.sh             ablation students on NS-50
  summarise_main.py              main_table.{md,tex,tsv}
  summarise_ablation.py          ablation_table.{md,tex,tsv}
  make_full_table.py             the full 50-isolate table
  paper_stats.py                 spread / correlation statistics quoted in the text
  throughput_benchmark.py        reads/s (encoder + shared pure-PyTorch Viterbi)
  benchmark_throughput.py        encoder-only vs. end-to-end breakdown
  status.sh                      progress dashboard
m2caller/                shared basecaller code (student architectures, data, decoding, utils)
logs/                    per-isolate results behind every model in Tables I-II
  bonito_sup_all.csv     Bonito sup (R9.4.1 v3.3), all 50 isolates
  bonito_hac_all.csv     Bonito hac
  dorado_sup_all.csv     Dorado sup
  phase2/eval50_*.csv    the four compact students
  phase2/main_table.*    generated summary tables
checkpoints_kd/          the four compact students evaluated in Table II (best.pt + training curves)
figures/                 figure-generation scripts and the paper PDFs
```

## Install

The decoder is pure PyTorch, but the evaluation harness reads FAST5 and loads
Bonito/Dorado checkpoints:

```bash
pip install torch numpy editdistance ont-fast5-api
pip install ont-bonito          # for bonito.reader / bonito.util model loading
```

Then make the bundled `koi` package importable **instead of** ONT's:

```bash
export PYTHONPATH="$PWD:$PYTHONPATH"
python -c "import koi.ctc; print(koi.ctc.__doc__.splitlines()[1])"
```

No `koi` CUDA build, and no closed-source kernel, is required at any point.

## Data and vendor checkpoints

Neither the corpus nor the ONT checkpoints are redistributed here:

- **Corpus** — the public Wick *et al.* bacterial nanopore set (50 isolates,
  13 genera), with assemblies used as per-read reference anchors.
- **Vendor checkpoints** — `dna_r9.4.1_e8_sup@v3.3` / `hac@v3.3` via
  `bonito download --models`, and `dna_r9.4.1_e8_sup@v3.6` via
  `dorado download`.

The deterministic read-selection manifest means the exact evaluation reads are
recoverable from the corpus without re-running selection.

## Reproduce

```bash
export PYTHONPATH="$PWD:$PYTHONPATH"

# audit the ONT production checkpoints (Table I)
bash scripts/phase2/eval_dorado_sup_all.sh
bash scripts/phase2/eval_bonito_hac_all.sh

# evaluate the compact students on the same protocol (Table II)
bash scripts/phase2/eval_nanospecies50.sh

# tables, statistics and figures
python scripts/phase2/summarise_main.py
python scripts/phase2/make_full_table.py
python scripts/phase2/paper_stats.py
python figures/make_figures.py
python figures/make_spread.py
```

`logs/` already contains the per-isolate CSVs behind every published number, so
the tables, statistics and figures can be regenerated without any GPU or access
to the corpus.

`make_figures.py` is shared with the companion distillation paper: it writes this
paper's figures to `figures/` and the CRF-KD ones to
`figures/companion_crf_kd/` (untracked).

The shell drivers under `scripts/` call `${PY:-python3}`, so point `PY` at the
interpreter you want:

```bash
PY=/path/to/venv/bin/python bash scripts/phase2/eval_dorado_sup_all.sh
```

## Scoring a new checkpoint

The harness loads the checkpoint, runs the deterministic read-selection protocol
against the manifest, decodes every read with the audited Viterbi
implementation, and reports per-isolate medians plus the median-of-medians and
cross-isolate spread. There are no seeds and no manual read curation, so a new
model can be slotted in as an additional column without bespoke engineering.

## Main findings

- Bonito sup's headline accuracy hides a **6.4 pp per-isolate spread**, including
  a **5.4 pp intra-genus spread** within *K. pneumoniae*.
- The spread persists across vendor checkpoints (pairwise rho >= 0.987 across two
  architectures) and across model sizes, so it is a property of the training
  corpus rather than of any one checkpoint.
- Compact students inherit their teacher's per-isolate weaknesses rather than
  averaging them away; hard-only M2-Small beats distilled M2-Small on every
  isolate while distilled M2-Tiny wins on 48/50 — a capacity crossover that
  pooled accuracy hides entirely.
- Building the decoder surfaced a silent reimplementation bug that severely
  corrupted accuracy while leaving no obvious trace, which is why the benchmark
  ships an audited reference decoder.
