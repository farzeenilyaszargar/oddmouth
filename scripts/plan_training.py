"""Generate a hardware-aware planning report without downloading data or weights.

python3 scripts/plan_training.py --output reports/mac_training_preflight.json
All parameter/memory counts are analytic estimates, not a model benchmark.
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


def linear(inputs, outputs):
    return inputs * outputs + outputs


def norm(width):
    return 2 * width


def parameter_estimate(config):
    """Explicit hypothetical dense blocks: no claim of implemented module counts."""
    a = config["expanded_candidate"]
    text, flow = a["text_width"], a["flow_width"]
    text_block = (4 * linear(text, text) + linear(text, a["text_ffn_width"])
                  + linear(a["text_ffn_width"], text) + 2 * norm(text))
    # Self-attention + cross-attention + FFN; three layer norms per flow block.
    flow_block = (8 * linear(flow, flow) + linear(flow, a["flow_ffn_width"])
                  + linear(a["flow_ffn_width"], flow) + 3 * norm(flow))
    mel = config["audio"]["mel_bins"]
    # Two kernel-3 conv layers, layer norms, and one scalar duration head.
    duration_head = 2 * (3 * text * text + text + norm(text)) + linear(text, 1)
    modules = {
        "phoneme_embedding": a["phoneme_vocab_size"] * text,
        "text_encoder": a["text_layers"] * text_block + norm(text),
        "text_projection": linear(text, flow),
        "duration_head": duration_head,
        "pitch_energy_heads": 2 * (linear(text, 128) + linear(128, 1)),
        "emotion_embedding_and_projection": a["emotion_count"] * a["emotion_width"]
            + linear(a["emotion_width"], flow),
        "time_embedding_mlp": linear(a["time_width"], flow) + linear(flow, flow),
        "mel_input_output": linear(mel, flow) + linear(flow, mel) + norm(flow),
        "conditional_flow_decoder": a["flow_layers"] * flow_block,
        "vocoder_reservation_not_counted_weights": a["vocoder_parameter_reservation"],
    }
    return modules


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
    modules = parameter_estimate(config)
    total = sum(modules.values())
    trainable_upper = total - config["expanded_candidate"]["vocoder_parameter_reservation"]
    storage = config["storage"]
    allocation_keys = ["active_features_bytes", "persistent_eval_bytes", "replay_bytes",
                       "raw_episode_bytes", "temporary_bytes", "metadata_bytes"]
    if sum(storage[k] for k in allocation_keys) > storage["managed_data_cache_bytes"]:
        raise ValueError("Concurrent data allocations exceed managed cache")
    if total > config["parameter_limit"]:
        raise ValueError("Expanded candidate exceeds complete parameter limit")
    audio = config["audio"]
    feature_rate = audio["mel_bins"] * audio["sample_rate"] / audio["hop_length"] * audio["mel_feature_bytes_per_value"]
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Analytic plan and observed hardware only; no MPS training benchmark",
        "hardware": hardware,
        "proposed_expanded_parameters_by_module": modules,
        "proposed_expanded_parameter_total": total,
        "actual_implemented_model_parameter_count": None,
        "parameter_headroom": config["parameter_limit"] - total,
        "weights_only_bytes": {"fp32": total * 4, "fp16": total * 2, "int8_ideal": total},
        "fp32_adam_memory_estimate": {
            "parameters_gradients_two_moments_upper_bytes": trainable_upper * 16,
            "frozen_vocoder_weights_bytes": config["expanded_candidate"]["vocoder_parameter_reservation"] * 4,
            "excludes": "Activations, allocator, runtime, CPU/GPU copies and other applications",
        },
        "storage_arithmetic": {
            "fifty_hours_pcm16_bytes": 50 * 3600 * audio["sample_rate"] * 2,
            "fifty_hours_fp16_mel_bytes_approx": round(50 * 3600 * feature_rate),
            "active_feature_shard_audio_hours_approx": storage["active_features_bytes"] / feature_rate / 3600,
            "note": "Payload estimates before headers, padding, other features or compression",
        },
        "download_chunk_cap_bytes": storage["max_download_chunk_bytes"],
        "concurrent_managed_cache_allocations_bytes": {k: storage[k] for k in allocation_keys},
        "concurrent_managed_cache_total_bytes": sum(storage[k] for k in allocation_keys),
        "minimum_disk_reserve_satisfied_now": disk.free >= storage["minimum_free_disk_bytes"],
        "speech_audio_downloads_performed": False,
        "training_started": False,
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
