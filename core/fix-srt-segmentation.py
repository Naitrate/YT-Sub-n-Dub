#!/usr/bin/env python3
"""
SRT Subtitle Segmentation Fixer (Final Comprehensive Version)

Handles all edge cases:
- Hyphenated word splits (e.g., "three" / "-dimensionally")
- Missing punctuation between separate thoughts
- Period-only entries
- Missing spaces after punctuation
- Contractions split across entries
- Incomplete clauses ending with commas
"""

import re
import sys
from typing import List


class SubtitleEntry:
    """Represents a single subtitle entry"""
    
    def __init__(self, index: int, start_time: str, end_time: str, text: str):
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text.strip()
    
    def __str__(self):
        return f"{self.index}\n{self.start_time} --> {self.end_time}\n{self.text}\n"


def parse_srt(content: str) -> List[SubtitleEntry]:
    """Parse SRT content into subtitle entries"""
    entries = []
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        try:
            index = int(lines[0])
            timing = lines[1]
            text = ' '.join(lines[2:])
            
            # Parse timing
            match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timing)
            if match:
                start_time, end_time = match.groups()
                entries.append(SubtitleEntry(index, start_time, end_time, text))
        except (ValueError, IndexError):
            continue
    
    return entries


def fix_spacing(text: str) -> str:
    """Fix spacing issues after punctuation"""
    # Add space after comma if missing
    text = re.sub(r',([a-zA-Z])', r', \1', text)
    # Add space after period if missing (but not in ellipsis)
    text = re.sub(r'\.([a-zA-Z])', r'. \1', text)
    # Remove space before punctuation
    text = re.sub(r'\s+([,.])', r'\1', text)
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def should_merge_with_next(current_text: str, next_text: str) -> bool:
    """
    Determine if current entry should be merged with the next one.
    
    Comprehensive criteria:
    - Next starts with hyphen (split hyphenated word)
    - Current is just punctuation
    - Next starts with contraction continuation
    - Next starts with period followed by capital
    - Current ends with comma
    - Current doesn't end with punctuation AND next starts lowercase
    - Current is very short without proper ending
    """
    if not current_text or not next_text:
        return True
    
    current_text = current_text.strip()
    next_text = next_text.strip()
    
    # Merge if next starts with hyphen (split hyphenated word like "-dimensionally")
    if next_text.startswith('-'):
        return True
    
    # Merge if current is just punctuation
    if len(current_text) <= 3 and not any(c.isalnum() for c in current_text):
        return True
    
    # Merge if next starts with contraction continuation
    contraction_starters = ["'s", "'re", "'ll", "'ve", "'d", "'m", "n't"]
    if any(next_text.startswith(cont) for cont in contraction_starters):
        return True
    
    # Merge if next starts with period then capital (bad split like ".And")
    if re.match(r'^\.+[A-Z]', next_text):
        return True
    
    # Check sentence-ending punctuation
    sentence_enders = {'.', '!', '?'}
    ends_with_sentence_end = current_text[-1] in sentence_enders if current_text else False
    
    # Check if current ends with comma (incomplete clause)
    ends_with_comma = current_text[-1] == ',' if current_text else False
    
    # Check if next starts lowercase
    starts_lowercase = next_text[0].islower() if next_text else False
    
    # Count words in current
    word_count = len(current_text.split())
    
    # Merge conditions:
    # 1. Ends with comma (incomplete)
    if ends_with_comma:
        return True
    
    # 2. Doesn't end with sentence punctuation AND next starts lowercase
    if not ends_with_sentence_end and starts_lowercase:
        return True
    
    # 3. Very short entry without proper ending
    if word_count <= 3 and not ends_with_sentence_end:
        return True
    
    return False


def needs_period_between(current_text: str, next_text: str) -> bool:
    """
    Check if we need to add a period between current and next when merging
    separate thoughts.
    
    Returns True if:
    - Current doesn't end with punctuation
    - Next starts with a capital letter (new thought)
    - Current has substantial content (not just a fragment)
    """
    if not current_text or not next_text:
        return False
    
    current_text = current_text.strip()
    next_text = next_text.strip()
    
    # Check if current ends with punctuation
    sentence_enders = {'.', '!', '?', ','}
    ends_with_punct = current_text[-1] in sentence_enders if current_text else False
    
    # Check if next starts with capital
    starts_capital = next_text[0].isupper() if next_text else False
    
    # Check if current has substantial content (more than 3 words)
    word_count = len(current_text.split())
    
    # Add period if: no ending punctuation, substantial content, next starts with capital
    return not ends_with_punct and word_count > 3 and starts_capital


def clean_merged_text(text: str) -> str:
    """Clean up merged text"""
    # Remove leading period if followed by capital letter
    text = re.sub(r'^\.\s*([A-Z])', r'\1', text)
    
    # Fix spacing
    text = fix_spacing(text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def merge_entries(entries: List[SubtitleEntry]) -> List[SubtitleEntry]:
    """Merge subtitle entries that should be combined"""
    if not entries:
        return []
    
    merged = []
    i = 0
    
    while i < len(entries):
        current = entries[i]
        merged_text = current.text
        end_time = current.end_time
        
        # Look ahead and merge consecutive entries
        j = i + 1
        while j < len(entries):
            next_entry = entries[j]
            
            if not should_merge_with_next(merged_text, next_entry.text):
                # Check if we should add a period between separate thoughts
                if needs_period_between(merged_text, next_entry.text):
                    if not merged_text.endswith('.'):
                        merged_text = merged_text.rstrip() + '.'
                break
            
            # Determine spacing between merged parts
            merged_text_stripped = merged_text.rstrip()
            next_text_stripped = next_entry.text.lstrip()
            
            # Check if we need a space
            needs_space = True
            if merged_text_stripped and next_text_stripped:
                # No space if next starts with punctuation, contraction, or hyphen
                if next_text_stripped[0] in "',.!?-":
                    needs_space = False
            
            # Merge the text
            if needs_space and merged_text_stripped and next_text_stripped:
                merged_text = merged_text_stripped + ' ' + next_text_stripped
            else:
                merged_text = merged_text_stripped + next_text_stripped
            
            end_time = next_entry.end_time
            j += 1
        
        # Clean up the merged text
        merged_text = clean_merged_text(merged_text)
        
        # Create merged entry if text is not empty
        if merged_text:
            merged_entry = SubtitleEntry(
                index=len(merged) + 1,
                start_time=current.start_time,
                end_time=end_time,
                text=merged_text
            )
            merged.append(merged_entry)
        
        i = j
    
    return merged


def fix_srt_file(input_path: str, output_path: str = None) -> None:
    """
    Fix segmentation issues in an SRT file
    
    Args:
        input_path: Path to input SRT file
        output_path: Path to output SRT file (defaults to input_fixed.srt)
    """
    if output_path is None:
        base = input_path.replace('.srt', '').replace('_enhanced_fixed', '').replace('_fixed', '')
        output_path = f"{base}_fixed.srt"
    
    # Read input file
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Parse entries
    entries = parse_srt(content)
    print(f"📄 Parsed {len(entries)} subtitle entries")
    
    # Merge entries
    merged_entries = merge_entries(entries)
    reduction = len(entries) - len(merged_entries)
    reduction_pct = (reduction / len(entries) * 100) if entries else 0
    
    print(f"✅ Merged into {len(merged_entries)} subtitle entries")
    print(f"📊 Reduced by {reduction} entries ({reduction_pct:.1f}%)")
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in merged_entries:
            f.write(str(entry))
            f.write('\n')
    
    print(f"\n💾 Fixed SRT file saved to: {output_path}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("SRT Subtitle Segmentation Fixer")
        print("=" * 60)
        print("\nUsage: python fix_srt_final.py <input.srt> [output.srt]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_srt_file(input_file, output_file)


if __name__ == '__main__':
    main()
