from typing import List, Dict, Any, Tuple
from thefuzz import fuzz
import difflib

def diff_blocks(old_blocks: List[Tuple[str, str]], new_blocks: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    Compares two lists of semantic blocks (role, text).
    Returns a summary of additions, deletions, and modifications.
    """
    old_texts = [text for role, text in old_blocks]
    new_texts = [text for role, text in new_blocks]
    
    # autojunk=False prevents difflib from ignoring common words/characters
    # which is crucial for high-fidelity text reconciliation.
    sm = difflib.SequenceMatcher(None, old_texts, new_texts, autojunk=False)
    
    additions = []
    deletions = []
    modifications = []
    
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'replace':
            # Could be a modification or a complete rewrite
            for i, j in zip(range(i1, i2), range(j1, j2)):
                score = fuzz.ratio(old_texts[i], new_texts[j])
                if score > 60:
                    modifications.append({
                        "old": old_texts[i],
                        "new": new_texts[j],
                        "confidence": score
                    })
                else:
                    deletions.append(old_texts[i])
                    additions.append(new_texts[j])
            # Handle unequal replacements
            if i2 - i1 > j2 - j1:
                for i in range(i1 + (j2 - j1), i2):
                    deletions.append(old_texts[i])
            elif j2 - j1 > i2 - i1:
                for j in range(j1 + (i2 - i1), j2):
                    additions.append(new_texts[j])
        elif tag == 'delete':
            for i in range(i1, i2):
                deletions.append(old_texts[i])
        elif tag == 'insert':
            for j in range(j1, j2):
                additions.append(new_texts[j])
                
    return {
        "additions": additions,
        "deletions": deletions,
        "modifications": modifications
    }

def evaluate_corrections(version_blocks: List[List[Tuple[str, str]]], intended_corrections: List[str]) -> List[Dict[str, Any]]:
    """
    Traces intended corrections across multiple versions to determine their final state.
    """
    results = []
    
    # Pre-extract texts for each version for faster searching
    version_texts = [[text for role, text in blocks] for blocks in version_blocks]
    
    for correction in intended_corrections:
        first_appearance = -1
        survives_to_end = False
        state = "not found"
        confidence = 0
        
        # 1. Find first appearance
        for i, texts in enumerate(version_texts):
            best_match = 0
            for text in texts:
                score = fuzz.partial_ratio(correction.lower(), text.lower())
                if score > best_match:
                    best_match = score
                    
            if best_match >= 85: # Threshold for "applied"
                first_appearance = i
                state = "applied"
                confidence = best_match
                break
                
        # 2. Check if it survives to the end
        if first_appearance != -1 and first_appearance < len(version_texts) - 1:
            final_texts = version_texts[-1]
            best_final_match = 0
            for text in final_texts:
                score = fuzz.partial_ratio(correction.lower(), text.lower())
                if score > best_final_match:
                    best_final_match = score
                    
            if best_final_match >= 85:
                survives_to_end = True
                state = "retained"
            elif best_final_match < 60:
                survives_to_end = False
                state = "reverted"
            else:
                survives_to_end = False
                state = "uncertain" # Between 60 and 85 is ambiguous
                
        elif first_appearance == len(version_texts) - 1:
            # Appeared in the very last version
            survives_to_end = True
            
        results.append({
            "correction": correction,
            "first_version_index": first_appearance if first_appearance != -1 else None,
            "survives_to_end": survives_to_end,
            "status": state,
            "confidence": confidence
        })
        
    return results

def generate_trust_report(filenames: List[str], version_blocks: List[List[Tuple[str, str]]], intended_corrections: List[str]) -> Dict[str, Any]:
    """
    Generates the final 6-part Trust Report structured JSON.
    """
    if len(version_blocks) < 2:
        raise ValueError("At least two versions are required for a trust report.")
        
    # 1. Version Chain Summary
    version_chain_summary = {
        "files_processed": len(filenames),
        "sequence": filenames,
        "warnings": []
    }
    
    # 2. Correction Timeline
    timeline = evaluate_corrections(version_blocks, intended_corrections)
    
    # 3. Meaningful Change Summary (All sequential pairs)
    diff_summaries = []
    for i in range(len(version_blocks) - 1):
        summary = diff_blocks(version_blocks[i], version_blocks[i+1])
        summary["source_file"] = filenames[i]
        summary["target_file"] = filenames[i+1]
        diff_summaries.append(summary)
    
    if len(version_blocks[-1]) == 0:
        version_chain_summary["warnings"].append("Warning: No text could be extracted from the final file. It might be an image-based PDF or empty.")
    if len(version_blocks[0]) == 0:
        version_chain_summary["warnings"].append("Warning: No text could be extracted from the source file. It might be an image-based PDF or empty.")
    
    # 5. Human Review Queue
    review_queue = [item for item in timeline if item["status"] == "uncertain" or item["confidence"] < 90 and item["status"] != "not found"]
    
    # 6. Evidence and Confidence (Attached to timeline items)
    # Already included in timeline objects
    
    # 4. Final File Recommendation (Simplified for linear chain)
    recommendation = {
        "preferred_candidate": filenames[-1],
        "reason": f"Most recent version with {len([c for c in timeline if c['status'] in ('applied', 'retained')])} out of {len(intended_corrections)} corrections applied.",
        "weaknesses": f"{len([c for c in timeline if c['status'] == 'reverted'])} corrections were reverted."
    }
    
    report = {
        "version_chain_summary": version_chain_summary,
        "correction_timeline": timeline,
        "meaningful_change_summaries": diff_summaries,
        "final_file_recommendation": recommendation,
        "human_review_queue": review_queue,
        "evidence_and_confidence": timeline
    }
    
    return report
