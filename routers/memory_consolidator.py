#!/usr/bin/env python3
"""
Bosly Gov v4 - Memory Consolidator Router
Summarizes overflow chat messages using LLM.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List

from routers.direct_llm import call_llm_direct


def consolidate_messages(messages: List[str]) -> Dict[str, object]:
    """
    Takes a list of chat messages (oldest from overflow).
    Sends them to the LLM for summarisation.
    Returns {"summary": str, "facts": list, "updatedAt": iso_string}
    """
    if not messages:
        return {
            "summary": "",
            "facts": [],
            "updatedAt": datetime.utcnow().isoformat() + "Z"
        }

    # Prepare input text
    input_text = "\n".join(messages)
    
    # LLM prompt for summarization and fact extraction
    system_prompt = (
        "You are a precise assistant that summarizes conversations and extracts key information. "
        "Given a chat log, provide a concise summary and list of important facts, decisions, or patterns. "
        "Respond ONLY with a valid JSON object containing exactly two keys: \"summary\" (string) and \"facts\" (array of strings). "
        "Do not include any extra text, explanation, or formatting."
    )
    user_prompt = f"Chat log to summarize:\n\n{input_text}"
    
    # Call LLM
    rc, response_text, error = call_llm_direct(
        system_prompt=system_prompt,
        user_message=user_prompt,
        timeout=120
    )
    
    # Process response
    summary = ""
    facts = []
    
    if rc == 0 and response_text:
        try:
            # Extract JSON from response (handle potential extra text)
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                data = json.loads(json_str)
                summary = str(data.get("summary", "")).strip()
                facts_list = data.get("facts", [])
                if isinstance(facts_list, list):
                    facts = [str(f).strip() for f in facts_list if isinstance(f, (str, int, float))]
                else:
                    facts = []
            else:
                raise ValueError("No JSON object found")
        except (json.JSONDecodeError, ValueError, KeyError):
            # Fallback if LLM response is not valid JSON
            pass
    
    # Fallback: use first 200 characters of joined messages
    if not summary:
        combined = " ".join(messages)
        summary = combined[:200].strip()
        if len(combined) > 200:
            summary += "..."
        facts = []
    
    return {
        "summary": summary,
        "facts": facts,
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    }
