def _build_space_map(text: str) -> tuple[str, list[int]]:
    """
    Internal helper function.
    Creates a compacted version of the text and a map of cumulative
    space counts for each non-space character.
    
    Returns:
        tuple[str, list[int]]: (compacted_text, space_map)
    """
    compacted_text = []
    space_map = []
    space_count = 0
    
    for char in text:
        if char.isspace():
            space_count += 1
        else:
            compacted_text.append(char)
            space_map.append(space_count)
            
    return "".join(compacted_text), space_map

def gapmap(original_text: str, spaced_needle: str) -> tuple[int, int] | None:
    """
    Finds a "needle" string (which may contain extra spaces) within the
    original_text and returns the (start, end) offsets of the match.

    Args:
        original_text: The full, original text to search within.
        spaced_needle: The string to search for, which may have 
                       extra spaces inserted.

    Returns:
        A tuple (start, end) of the match's offsets in the 
        original_text, or None if no match is found.
    """
    
    #Build the space map for the original text
    compacted_original, space_map = _build_space_map(original_text)

    #Compact the needle
    compacted_needle = "".join(c for c in spaced_needle if not c.isspace())
    
    if not compacted_needle:
        return None  # Cannot search for an empty string

    #Find the compacted match
    start_index = compacted_original.find(compacted_needle)
    
    if start_index == -1:
        return None  # Match not found

    #Adjust offsets using the space map
    end_index_compacted = start_index + len(compacted_needle)
    
    original_start = start_index + space_map[start_index]
    
    last_char_map_index = end_index_compacted - 1
    original_end = end_index_compacted + space_map[last_char_map_index]

    return (original_start, original_end)