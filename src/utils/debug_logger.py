import streamlit as st
import json
import os
import time
from datetime import datetime

class DebugLogger:
    """
    Sistema de Telemetria v52.0 para LessonAI.
    Registra eventos de layout em session_state e arquivo JSONL.
    """
    LOG_FILE = "logs/layout_debug.jsonl"
    MAX_UI_LOGS = 50

    @staticmethod
    def _init_storage():
        if not os.path.exists("logs"):
            os.makedirs("logs")
        if "layout_events" not in st.session_state:
            st.session_state.layout_events = []
        if "rerun_count" not in st.session_state:
            st.session_state.rerun_count = 0
            
    @staticmethod
    def log(event_type: str, origin: str, page_index: int = -1, panel_index: int = -1, 
            data_before: dict = None, data_after: dict = None, message: str = "", 
            is_anomaly: bool = False, extra: dict = None):
        DebugLogger._init_storage()
        
        timestamp = datetime.now().isoformat()
        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "origin": origin,
            "page_index": page_index,
            "panel_index": panel_index,
            "data_before": data_before,
            "data_after": data_after,
            "message": message,
            "is_anomaly": is_anomaly,
            "rerun_id": st.session_state.rerun_count,
            "extra": extra or {}
        }
        
        # 1. Log para Session State (para o Painel UI)
        st.session_state.layout_events.insert(0, event)
        if len(st.session_state.layout_events) > DebugLogger.MAX_UI_LOGS:
            st.session_state.layout_events.pop()
            
        # 2. Log para Arquivo JSONL (Flush imediato para segurança forense)
        try:
            with open(DebugLogger.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                f.flush()
        except Exception as e:
            print(f"[DEBUG_LOGGER] Erro ao gravar arquivo: {e}")

    @staticmethod
    def increment_rerun():
        DebugLogger._init_storage()
        st.session_state.rerun_count += 1
        DebugLogger.log("STREAMLIT_RERUN", "system", message=f"Rerun #{st.session_state.rerun_count}")

    @staticmethod
    def get_events(limit: int = 10):
        DebugLogger._init_storage()
        return st.session_state.layout_events[:limit]
