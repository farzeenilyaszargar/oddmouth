"""Report real Oddmouth parameter counts and hardware; downloads nothing.

python3 scripts/plan_training.py --output reports/mac_training_preflight.json
Memory figures exclude activations; this is not a training benchmark.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def command(*args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def parameter_counts(config):
    """Instantiate the real modules (random weights) and count parameters."""
    import sys
    sys.path.insert(0, str(ROOT))
    from oddmouth.model import AcousticModel, Vocoder, Discriminators, count
    from oddmouth.text import VOCAB_SIZE
    a = config["architecture"]
    return {
        "acoustic_model": count(AcousticModel(a, VOCAB_SIZE)),
        "vocoder": count(Vocoder(a)),
    }, count(Discriminators())


def build_report(config):
    disk = shutil.disk_usage(ROOT)
    hardware = {
        "architecture": platform.machine(),
        "machine_model": command("sysctl", "-n", "hw.model"),
        "chip": command("sysctl", "-n", "machdep.cpu.brand_string"),
        "cpu_cores": command("sysctl", "-n", "hw.ncpu"),
        "unified_memory_bytes": command("sysctl", "-n", "hw.memsize"),
        "macos_version": command("sw_vers", "-productVersion"),
        "disk_free_bytes": disk.free,
        "memory_pressure_snapshot": command("memory_pressure", "-Q"),
        "swap_snapshot": command("sysctl", "vm.swapusage"),
        "identifier_policy": "No serial number, hardware UUID, or provisioning identifier collected",
    }
    for key in ["cpu_cores", "unified_memory_bytes"]:
        if hardware[key] is not None:
            hardware[key] = int(hardware[key])
    modules, discriminators = parameter_counts(config)
    total = sum(modules.values())
    storage = config["storage"]
    if total > config["parameter_limit"]:
        raise ValueError("Deployed model exceeds parameter limit")
    audio = config["audio"]
    feature_rate = audio["mel_bins"] * audio["sample_rate"] / audio["hop_length"] * audio["mel_feature_bytes_per_value"]
    hours = 10.8
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Real module parameter counts and observed hardware; not a training benchmark",
        "hardware": hardware,
        "deployed_parameters_by_module": modules,
        "deployed_parameter_total": total,
        "parameter_limit": config["parameter_limit"],
        "training_only_discriminator_parameters": discriminators,
        "training_scope": config["training_scope"],
        "weights_only_bytes": {"fp32": total * 4, "fp16": total * 2, "int8_ideal": total},
        "fp32_adam_bytes_excluding_activations": {
            "acoustic": modules["acoustic_model"] * 16,
            "vocoder_plus_discriminators": (modules["vocoder"] + discriminators) * 16,
        },
        "dailytalk_male_storage_estimate_bytes": {
            "fp16_mel": round(hours * 3600 * feature_rate),
            "pcm16_wave_all_clips": round(hours * 3600 * audio["sample_rate"] * 2),
            "pcm16_wave_kept_for_vocoder": round(hours * 3600 * audio["sample_rate"] * 2 * storage["vocoder_wave_fraction"]),
        },
        "download_chunk_cap_bytes": storage["max_download_chunk_bytes"],
        "managed_data_cache_bytes": storage["managed_data_cache_bytes"],
        "minimum_disk_reserve_satisfied_now": disk.free >= storage["minimum_free_disk_bytes"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/mac_training.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(json.loads(args.config.read_text()))
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded)


if __name__ == "__main__":
    main()
