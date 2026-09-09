"""
parser_logcat.py
-----------------
Lê um arquivo de log exportado (formato JSON do Logcat)
e extrai as linhas da tag DATASET_NEURO_FUZZY em um pandas.DataFrame.

Suporta os três formatos de log já utilizados no projeto:

  Formato original (7 campos):
    frame,RTT_ms,proc_ms,detect_ms,num_objetos,label_principal,score_principal

  Formato com pipeline desacoplado (8 campos):
    frame_id,rtt_rede_ms,espera_fila_ms,deteccao_ms,latencia_total_ms,
    num_objetos,label,score

  Formato atual, com proximidade real do obstáculo (9 campos):
    frame_id,rtt_rede_ms,espera_fila_ms,deteccao_ms,latencia_total_ms,
    num_objetos,label,score,proximidade (razão altura_caixa/altura_frame)
"""

import json
import pandas as pd


def load_dataset_from_logcat(filepath: str) -> pd.DataFrame:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("logcatMessages", [])
    rows = []

    for m in messages:
        if m.get("header", {}).get("tag") != "DATASET_NEURO_FUZZY":
            continue

        parts = m["message"].strip().split(",")

        if len(parts) == 9:
            frame_id, rtt, wait, detect, total, n_obj, label, score, proximity = parts
            rows.append({
                "frame_id": int(frame_id),
                "rtt_ms": int(rtt),
                "wait_ms": int(wait),
                "detect_ms": int(detect),
                "total_latency_ms": int(total),
                "num_objects": int(n_obj),
                "label": label,
                "score": float(score),
                "proximity": float(proximity),
            })
        elif len(parts) == 8:
            frame_id, rtt, wait, detect, total, n_obj, label, score = parts
            rows.append({
                "frame_id": int(frame_id),
                "rtt_ms": int(rtt),
                "wait_ms": int(wait),
                "detect_ms": int(detect),
                "total_latency_ms": int(total),
                "num_objects": int(n_obj),
                "label": label,
                "score": float(score),
                "proximity": None,  # não disponível neste formato de log
            })
        elif len(parts) == 7:
            # Formato antigo: sem coluna de fila nem de proximidade.
            frame_id, rtt, proc, detect, n_obj, label, score = parts
            rtt_i, detect_i = int(rtt), int(detect)
            rows.append({
                "frame_id": int(frame_id),
                "rtt_ms": rtt_i,
                "wait_ms": 0,
                "detect_ms": detect_i,
                "total_latency_ms": rtt_i + detect_i,
                "num_objects": int(n_obj),
                "label": label,
                "score": float(score),
                "proximity": None,
            })
        else:
            continue  # linha em formato inesperado, ignora

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("frame_id").reset_index(drop=True)
    return df


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_log.logcat"
    df = load_dataset_from_logcat(path)
    print(f"Linhas carregadas: {len(df)}")
    print(f"Tem coluna de proximidade real: {df['proximity'].notna().any() if not df.empty else 'N/A'}")
    print(df.head(10))
    print(df.describe())

