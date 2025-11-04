import os
import json

CANDIDATE_NODE = []
                
def find_candidate_node(code_project_dir):
    input_path = os.path.join(code_project_dir, "AST", "output", "inheritance_node.json")
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            node = item.get("node") or {}
            if "B_kind" not in node:
                extension = item.get("extension") or []
                children = item.get("children") or []
                for ext in extension:
                    if ext not in CANDIDATE_NODE:
                        CANDIDATE_NODE.append(ext)
                for child in children:
                    if child not in CANDIDATE_NODE:
                        CANDIDATE_NODE.append(child)
            elif node.get("B_kind") == "extension":
                if item not in CANDIDATE_NODE:
                    CANDIDATE_NODE.append(item)
    
    input_path = os.path.join(code_project_dir, "AST", "output", "no_inheritance_node.json")
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            if "B_kind" == "extension":
                if item not in CANDIDATE_NODE:
                    CANDIDATE_NODE.append(item)

def find_external_candidates(code_project_dir):
    find_candidate_node(code_project_dir)
    output_path = os.path.join(code_project_dir, "AST", "output", "external_candidates.json")
    with open(output_path, "a", encoding="utf-8") as f:
        json.dump(CANDIDATE_NODE, f, indent=2, ensure_ascii=False)
