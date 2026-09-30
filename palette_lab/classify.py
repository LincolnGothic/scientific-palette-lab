import re


def suggest_kind(caption):
    text = caption.lower()
    flow = bool(re.search(r"\b(flow\s?chart|workflow|decision tree|study design|analysis pipeline|experimental design)\b", text))
    data = bool(re.search(r"\b(bar plot|scatter|box\s?plot|heat\s?map|histogram|violin|survival curve|line plot|distribution)\b", text))
    if flow and data:
        return {"kind": "unknown", "reason": "Caption describes both diagrams and data plots; split and review panels."}
    if flow:
        return {"kind": "flowchart", "reason": "Caption keyword suggestion; confirm the panel visually."}
    if data:
        return {"kind": "data", "reason": "Caption keyword suggestion; confirm the panel visually."}
    return {"kind": "unknown", "reason": "No reliable caption hint; classification requires visual review."}
