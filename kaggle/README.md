# Training on Kaggle

[`oddmouth-train.ipynb`](oddmouth-train.ipynb) trains both models on a free Kaggle GPU. Kaggle currently offers about 30 GPU hours a week, with sessions of up to 12 hours. Kaggle keeps a version's output only if it finishes, so the notebook trains for 4 hours per version; chain versions to train longer.

## One-time setup

1. Create a Kaggle account, then verify your phone number under **Settings → Phone verification**. GPUs and internet access need it.
2. Optional, to continue from local checkpoints: zip them from the repository root:

   ```bash
   cd runs && zip -0 ../outputs/kaggle-upload/oddmouth-checkpoints.zip acoustic/last.pt vocoder/last.pt
   ```

   Then go to **Datasets → New Dataset**, upload the zip, set it to **Private**, and create it.

## Each training session

1. Go to **Code → New Notebook → File → Import Notebook** and upload `kaggle/oddmouth-train.ipynb` (only the first time).
2. In the right-hand panel, set **Accelerator** to **GPU T4 x2** and **Internet** to **On**.
3. Under **Add Input**, attach your checkpoint dataset, or the output of the notebook's previous version. Skip this to start from random weights.
4. Click **Save Version → Save & Run All (Commit)**. It runs in the background, so you can close the tab.
5. When it finishes, open the version's **Output** tab and download `runs/acoustic/last.pt` and `runs/vocoder/last.pt`. Listening samples are in `runs/*/samples/`.

To keep training, start a new version with the previous version's output attached as input. The notebook resumes from the highest step it finds.

To listen locally, put the downloaded files in `runs/acoustic/` and `runs/vocoder/`, then export a preview (see [web/README.md](../web/README.md)).

## Notes

- The notebook trains the acoustic model and the vocoder in parallel, one per GPU when two are available. Batches are larger than on a Mac (`training.cuda` in `configs/oddmouth.json`).
- Log lines include `host_rss_mb` and `host_available_mb` (Linux), to diagnose a run that stops without an error.
- Keep notebooks, datasets and outputs **private**. DailyTalk is not cleared for commercial use. Do not upload audio whose training rights are unclear.
