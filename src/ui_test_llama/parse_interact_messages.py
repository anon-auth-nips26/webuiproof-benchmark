#!/usr/bin/env python3
import glob
import json
import re
import os
from collections import defaultdict

def process_element_match(element_id, element_name, description, interactive):
    """
    Process an element match and handle ID ranges.
    
    Args:
        element_id (str): Element ID
        element_name (str): Element name
        description (str): Element description
        interactive (bool): Whether the element is interactive
        
    Returns:
        list: List of element dictionaries
    """
    elements = []
    
    # Handle element IDs that represent ranges (e.g., "C1-C4")
    if "-" in element_id:
        # Split only on the first hyphen to handle IDs with multiple hyphens
        parts = element_id.split("-", 1)
        if len(parts) == 2:
            start_id, end_id = parts
        else:
            # If splitting doesn't result in exactly 2 parts, treat as a single element
            elements.append({
                "id": element_id,
                "name": element_name,
                "description": description,
                "interactive": interactive
            })
            return elements
        # Extract the prefix and numeric parts
        start_prefix = ''.join(c for c in start_id if not c.isdigit())
        end_prefix = ''.join(c for c in end_id if not c.isdigit())
        
        try:
            start_num = int(''.join(c for c in start_id if c.isdigit()) or 0)
            end_num = int(''.join(c for c in end_id if c.isdigit()) or 0)
            
            # Only process if prefixes match
            if start_prefix == end_prefix:
                for i in range(start_num, end_num + 1):
                    elements.append({
                        "id": f"{start_prefix}{i}",
                        "name": element_name,
                        "description": description,
                        "interactive": interactive
                    })
            else:
                # If prefixes don't match, just add as a single element
                elements.append({
                    "id": element_id,
                    "name": element_name,
                    "description": description,
                    "interactive": interactive
                })
        except ValueError:
            # If conversion to int fails, just add as a single element
            elements.append({
                "id": element_id,
                "name": element_name,
                "description": description,
                "interactive": interactive
            })
    else:
        elements.append({
            "id": element_id,
            "name": element_name,
            "description": description,
            "interactive": interactive
        })
    
    return elements

def extract_ui_elements(content):
    """
    Extract UI elements from the UI Observations section of a thought.
    
    Args:
        content (str): The content of an assistant message
        
    Returns:
        list: List of dictionaries containing element information
    """
    # Find the UI Observations section
    ui_obs_match = re.search(r'2\.\s+UI\s+Observations:(.*?)(?:3\.\s+Interaction|$)', content, re.DOTALL)
    if not ui_obs_match:
        return []
    
    ui_obs_text = ui_obs_match.group(1)
    
    # Extract individual elements
    elements = []
    
    # Extract elements using patterns that handle different formats
    # Pattern 1: * [ID] - [Name] Description [Interactive: Yes/No]
    element_pattern1 = r'\*\s+\[([^\]]+)\]\s+-\s+\[([^\]]+)\](.*?)\[Interactive:\s+(Yes|No)\]'
    
    # Pattern 2: * [ID] - Name: Description [Interactive: Yes/No]
    element_pattern2 = r'\*\s+\[([^\]]+)\]\s+-\s+([^:\[]+)(?::\s*([^\[]*?))?\s*\[Interactive:\s+(Yes|No)\]'
    
    # Pattern 3: - [index] - [Name] Description [Interactive: Yes/No]
    # This handles the format: - [0] - [Services] Navigation link for services [Interactive: Yes]
    element_pattern3 = r'-\s+\[([^\]]+)\]\s+-\s+\[([^\]]+)\]\s+(.*?)\[Interactive:\s+(Yes|No)\]'
    
    # Process elements matching pattern 1 (with asterisk and brackets around name)
    for match in re.finditer(element_pattern1, ui_obs_text, re.DOTALL):
        element_id = match.group(1).strip()
        element_name = match.group(2).strip()
        description = match.group(3).strip() if match.group(3) else ""
        interactive = match.group(4) == "Yes"
        
        # Add to elements list
        elements_to_add = process_element_match(element_id, element_name, description, interactive)
        elements.extend(elements_to_add)
    
    # Process elements matching pattern 2 (with asterisk but without brackets around name)
    for match in re.finditer(element_pattern2, ui_obs_text, re.DOTALL):
        element_id = match.group(1).strip()
        element_name = match.group(2).strip()
        description = match.group(3).strip() if match.group(3) else ""
        interactive = match.group(4) == "Yes"
        
        # Add to elements list
        elements_to_add = process_element_match(element_id, element_name, description, interactive)
        elements.extend(elements_to_add)
    
    # Process elements matching pattern 3 (with dash instead of asterisk)
    for match in re.finditer(element_pattern3, ui_obs_text, re.DOTALL):
        element_id = match.group(1).strip()
        element_name = match.group(2).strip()
        description = match.group(3).strip() if match.group(3) else ""
        interactive = match.group(4) == "Yes"
        
        # Add to elements list
        elements_to_add = process_element_match(element_id, element_name, description, interactive)
        elements.extend(elements_to_add)
    
    # Also look for grouped elements pattern (e.g., [3-6] - Text elements within [C5] - [Financial Metrics Card])
    grouped_pattern = r'\*\s+\[([^\]]+)\]\s+-\s+(.*?)within\s+\[([^\]]+)\]\s+-\s+\[([^\]]+)\]'
    
    for match in re.finditer(grouped_pattern, ui_obs_text, re.DOTALL):
        if match and len(match.groups()) >= 4:
            element_ids = match.group(1).strip()
            text_description = match.group(2).strip() if match.group(2) else ""
            container_id = match.group(3).strip()
            container_name = match.group(4).strip()
            
            # Handle element IDs that represent ranges
            if "-" in element_ids:
                start_id, end_id = element_ids.split("-")
                try:
                    start_num = int(start_id)
                    end_num = int(end_id)
                    for i in range(start_num, end_num + 1):
                        elements.append({
                            "id": str(i),
                            "name": f"Text element in {container_name}",
                            "description": f"{text_description} within {container_name}",
                            "interactive": False,
                            "container_id": container_id,
                            "container_name": container_name
                        })
                except ValueError:
                    # If not numeric IDs, just add as a group
                    elements.append({
                        "id": element_ids,
                        "name": f"Text elements in {container_name}",
                        "description": f"{text_description} within {container_name}",
                        "interactive": False,
                        "container_id": container_id,
                        "container_name": container_name
                    })
    
    return elements

def extract_test_cases(content):
    """
    Extract test cases from the Test Case Suggestions section of a thought.
    
    Args:
        content (str): The content of an assistant message
        
    Returns:
        list: List of dictionaries containing test case information
    """
    # Find the Test Case Suggestions section
    test_case_section_patterns = [
        r'5\.\s+Test\s+Case\s+Suggestions:\s*(.*?)(?:Element Coverage Summary:|\n\nNext Steps:|$)',
        r'6\.\s+Test\s+Case\s+Suggestions:\s*(.*?)(?:Element Coverage Summary:|\n\nNext Steps:|$)',
        r'Test\s+Case\s+Suggestions:\s*(.*?)(?:Element Coverage Summary:|\n\nNext Steps:|$)'
    ]
    
    test_case_section = None
    for pattern in test_case_section_patterns:
        test_case_section = re.search(pattern, content, re.DOTALL)
        if test_case_section:
            break
    
    if not test_case_section:
        return []
    
    test_case_text = test_case_section.group(1)
    
    # Extract individual test cases
    test_cases = []
    
    # Pattern for test case headers - more flexible to match different formats
    # Format 1: **TC001 - Test Name**
    test_case_pattern1 = r'\*\*TC0*(\d+)\s*-\s*([^\*]+)\*\*'
    
    # Format 2: * TC001 - Test Name
    test_case_pattern2 = r'\*\s*TC0*(\d+)\s*-\s*([^\n]+)'
    
    # Find all test case headers using both patterns
    test_case_matches1 = list(re.finditer(test_case_pattern1, test_case_text))
    test_case_matches2 = list(re.finditer(test_case_pattern2, test_case_text))
    
    # Combine matches from both patterns
    all_matches = []
    for match in test_case_matches1:
        all_matches.append({
            'match': match,
            'format': 1,
            'start': match.start(),
            'test_id': match.group(1),
            'test_name': match.group(2).strip()
        })
    
    for match in test_case_matches2:
        all_matches.append({
            'match': match,
            'format': 2,
            'start': match.start(),
            'test_id': match.group(1),
            'test_name': match.group(2).strip()
        })
    
    # Sort matches by their position in the text
    all_matches.sort(key=lambda x: x['start'])
    
    # Process each test case
    for i, match_info in enumerate(all_matches):
        test_id = match_info['test_id']
        test_name = match_info['test_name']
        match = match_info['match']
        format_type = match_info['format']
        
        # Find the start position of this test case
        start_pos = match.start()
        
        # Find the end position (start of next test case or end of section)
        if i < len(all_matches) - 1:
            end_pos = all_matches[i + 1]['match'].start()
        else:
            end_pos = len(test_case_text)
        
        # Extract the content of this test case
        test_case_content = test_case_text[start_pos:end_pos]
        
        # Define patterns for both formats
        # Format 1 patterns (using - **Field:** value)
        format1_patterns = {
            'objective': r'-\s*\*\*Test\s+Objective:\*\*\s*(.*?)(?=-\s*\*\*|$)',
            'type': r'-\s*\*\*Test\s+Type:\*\*\s*(.*?)(?=-\s*\*\*|$)',
            'coverage': r'-\s*\*\*Coverage\s+Element:\*\*\s*(.*?)(?=-\s*\*\*|$)',
            'precond': r'-\s*\*\*Preconditions:\*\*\s*(.*?)(?=-\s*\*\*|$)',
            'procedure': r'-\s*\*\*Test\s+Procedure:\*\*\s*(.*?)(?=-\s*\*\*Expected|$)',
            'results': r'-\s*\*\*Expected\s+Results:\*\*\s*(.*?)(?=\n\n|$)'
        }
        
        # Format 2 patterns (using + Field: value)
        format2_patterns = {
            'objective': r'\+\s*Test\s+Objective:\s*(.*?)(?=\+|$)',
            'type': r'\+\s*Test\s+Type:\s*(.*?)(?=\+|$)',
            'coverage': r'\+\s*Coverage\s+Element:\s*(.*?)(?=\+|$)',
            'precond': r'\+\s*Preconditions:\s*(.*?)(?=\+|$)',
            'procedure': r'\+\s*Test\s+Procedure:\s*(.*?)(?=\+\s*Expected|$)',
            'results': r'\+\s*Expected\s+Results:\s*(.*?)(?=\n\n|$)'
        }
        
        # Try both formats regardless of the detected format type
        # This makes the parser more robust to mixed formats
        field_values = {
            'objective': "",
            'type': "",
            'coverage': "",
            'precond': "",
            'procedure': "",
            'results': ""
        }
        
        # Try all patterns from both formats
        for field, pattern in format1_patterns.items():
            match = re.search(pattern, test_case_content, re.DOTALL)
            if match and match.group(1).strip():
                field_values[field] = match.group(1).strip()
        
        for field, pattern in format2_patterns.items():
            if not field_values[field]:  # Only try if not already found
                match = re.search(pattern, test_case_content, re.DOTALL)
                if match and match.group(1).strip():
                    field_values[field] = match.group(1).strip()
        
        # Extract test objective
        objective = field_values['objective']
        
        # Extract test type
        test_type = field_values['type']
        
        # Extract coverage element
        coverage_element = field_values['coverage']
        
        # Extract preconditions
        preconditions = field_values['precond']
        
        # Extract test procedure
        procedure = field_values['procedure']
        
        # Extract steps from procedure
        steps = []
        if procedure:
            # Try multiple step patterns to handle different formats
            step_patterns = [
                # Format 1: Markdown numbered steps (1. Step description)
                r'\s*(\d+)\s*\.\s*(.*?)(?=\s*\d+\s*\.|\s*-\s*\*\*|$)',
                # Format 2: Bullet point steps (+ Step description or * Step description)
                r'(?:\+|\*)\s*(.*?)(?=(?:\+|\*)|\n\n|$)',
                # Format 3: Indented steps with numbers (  1. Step description)
                r'\s+\d+\.\s*(.*?)(?=\s+\d+\.|\n\n|$)',
                # Format 4: Simple numbered list (1. Step description)
                r'^\s*\d+\.\s*(.*?)$'
            ]
            
            # Try each pattern until we find steps
            for pattern in step_patterns:
                step_matches = list(re.finditer(pattern, procedure, re.DOTALL | re.MULTILINE))
                if step_matches:
                    for step_match in step_matches:
                        # Group index depends on the pattern
                        if len(step_match.groups()) > 1:  # If there are multiple groups
                            step_text = step_match.group(2).strip()
                        else:
                            step_text = step_match.group(1).strip()
                        
                        if step_text:  # Only add non-empty steps
                            steps.append(step_text)
                    break  # Stop after finding steps with one pattern
            
            # If no steps were found with the patterns, split by newlines as a fallback
            if not steps:
                for line in procedure.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('**'):
                        steps.append(line)
        
        # Extract expected results
        expected_results = field_values['results']
        
        # Only add test case if we have at least a name and objective
        if test_name and (objective or test_type or steps):
            test_cases.append({
                "id": f"TC{test_id}",
                "name": test_name,
                "objective": objective,
                "type": test_type,
                "coverage_element": coverage_element,
                "preconditions": preconditions,
                "procedure_steps": steps,
                "expected_results": expected_results
            })
    
    return test_cases

def parse_interact_messages(file_path):
    """
    Parse the interact_messages.json file to extract UI elements and test cases.
    
    Args:
        file_path (str): Path to the interact_messages.json file
        
    Returns:
        dict: Dictionary with UI elements and test cases
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    
    # Initialize result dictionary
    result = {
        "ui_elements": [],
        "test_cases": []
    }
    
    # Dictionary to track unique elements by ID
    unique_elements_by_id = {}
    
    # Extract UI elements and test cases from assistant messages
    for message in messages:
        if message.get("role") == "assistant" and "content" in message:
            content = message.get("content", "")
            
            # Extract UI elements
            elements = extract_ui_elements(content)
            for element in elements:
                # Skip "Unknown Card" elements
                if element["name"] == "Unknown Card":
                    continue
                    
                element_id = element["id"]
                # If this ID is already in our dictionary, decide which one to keep
                if element_id in unique_elements_by_id:
                    existing_element = unique_elements_by_id[element_id]
                    
                    # Compare element names
                    existing_name = existing_element["name"]
                    current_name = element["name"]
                    
                    # Prioritize more specific names over generic ones
                    # For example, prefer "Financial Metrics Card" over just "Card"
                    if "Card" in current_name and "Card" not in existing_name:
                        unique_elements_by_id[element_id] = element
                    elif "Card" in existing_name and "Card" not in current_name:
                        pass  # Keep the existing element
                    # If both have "Card" or neither has "Card", prefer the longer, more descriptive name
                    elif len(current_name) > len(existing_name):
                        unique_elements_by_id[element_id] = element
                else:
                    unique_elements_by_id[element_id] = element
            
            # Extract test cases
            test_cases = extract_test_cases(content)
            
            # Only add unique test cases based on name
            for test_case in test_cases:
                # Check if this test case name already exists
                if not any(tc["name"] == test_case["name"] for tc in result["test_cases"]):
                    result["test_cases"].append(test_case)
    
    # Group elements with the same name and description
    grouped_elements = {}
    id_groups = {}
    
    for element in unique_elements_by_id.values():
        # Create a key based on name and description
        key = f"{element['name']}_{element.get('description', '')}"
        
        if key in grouped_elements:
            # If we've seen this name+description before, add this ID to the group
            existing_element = grouped_elements[key]
            
            # Add this ID to the group
            if '-' in existing_element['id']:
                # Already a group, add this ID to the range
                id_parts = existing_element['id'].split('-')
                prefix = ''.join(c for c in id_parts[0] if not c.isdigit())
                
                # Extract current IDs in the group
                current_ids = []
                for id_part in id_parts:
                    if '-' in id_part:
                        start, end = id_part.split('-')
                        start_prefix = ''.join(c for c in start if not c.isdigit())
                        end_prefix = ''.join(c for c in end if not c.isdigit())
                        start_num = int(''.join(c for c in start if c.isdigit()) or 0)
                        end_num = int(''.join(c for c in end if c.isdigit()) or 0)
                        
                        if start_prefix == end_prefix:
                            for i in range(start_num, end_num + 1):
                                current_ids.append(f"{start_prefix}{i}")
                    else:
                        current_ids.append(id_part)
                
                # Add the new ID
                current_ids.append(element['id'])
                
                # Sort and group consecutive IDs
                current_ids.sort(key=lambda x: (x[0] if x[0].isalpha() else '', int(''.join(c for c in x if c.isdigit()) or 0)))
                
                # Create new ID string
                new_id = current_ids[0]
                if len(current_ids) > 1:
                    new_id += f"-{current_ids[-1]}"
                
                existing_element['id'] = new_id
            else:
                # Start a new group with this ID and the existing one
                existing_element['id'] = f"{existing_element['id']}-{element['id']}"
            
            # Store the group mapping
            id_groups[element['id']] = existing_element['id']
        else:
            # First time seeing this name+description
            grouped_elements[key] = element
            id_groups[element['id']] = element['id']
    
    # Update test cases to use grouped IDs
    for test_case in result["test_cases"]:
        if "coverage_element" in test_case and test_case["coverage_element"]:
            # Extract the element ID from the coverage element field
            coverage_match = re.search(r'\[(.*?)\]', test_case["coverage_element"])
            if coverage_match:
                element_id = coverage_match.group(1)
                if element_id in id_groups:
                    # Replace with the grouped ID
                    test_case["coverage_element"] = test_case["coverage_element"].replace(
                        f"[{element_id}]", f"[{id_groups[element_id]}]"
                    )
    
    # Add all grouped elements to the result
    result["ui_elements"] = list(grouped_elements.values())
    
    return result

def normalize_element_name(name):
    """
    Normalize element names to help identify similar elements.
    
    Args:
        name (str): Element name
        
    Returns:
        str: Normalized element name
    """
    # Remove common suffixes
    name = re.sub(r'\s+(Button|Tab|Card|Element)s?$', '', name, flags=re.IGNORECASE)
    # Remove specific company names
    name = re.sub(r'^(Apple Inc\.|Google|Microsoft|Amazon)\s+', '', name)
    # Handle singular/plural forms
    name = re.sub(r'(s)$', '', name)  # Remove trailing 's' for plurals
    # Convert to lowercase for case-insensitive comparison
    return name.lower()

def group_similar_elements(elements):
    """
    Group similar elements based on normalized names and IDs.
    
    Args:
        elements (list): List of UI elements
        
    Returns:
        list: List of grouped elements
    """
    # First, group by ID to identify elements that are definitely the same
    id_groups = {}
    for element in elements:
        # Extract the base ID (without ranges)
        base_id = element['id'].split('-', 1)[0] if '-' in element['id'] else element['id']
        
        if base_id not in id_groups:
            id_groups[base_id] = []
        id_groups[base_id].append(element)
    
    # Process each ID group
    id_processed_elements = []
    for base_id, id_elements in id_groups.items():
        if len(id_elements) > 1:
            # Multiple elements with the same base ID
            # Sort by description length (longer is more descriptive)
            id_elements.sort(key=lambda e: len(e.get('description', '')), reverse=True)
            best_element = id_elements[0]
            
            # Combine all IDs from this group
            all_ids = set()
            for e in id_elements:
                if '-' in e['id']:
                    parts = e['id'].split('-', 1)
                    if len(parts) == 2:
                        start, end = parts
                    else:
                        # If splitting doesn't result in exactly 2 parts, use the ID as is
                        all_ids.add(e['id'])
                        continue
                    start_prefix = ''.join(c for c in start if not c.isdigit())
                    end_prefix = ''.join(c for c in end if not c.isdigit())
                    start_num = int(''.join(c for c in start if c.isdigit()) or 0)
                    end_num = int(''.join(c for c in end if c.isdigit()) or 0)
                    
                    if start_prefix == end_prefix:
                        for i in range(start_num, end_num + 1):
                            all_ids.add(f"{start_prefix}{i}")
                else:
                    all_ids.add(e['id'])
            
            # Sort and create ranges
            all_ids = sorted(all_ids, key=lambda x: (x[0] if x[0].isalpha() else '', 
                                                int(''.join(c for c in x if c.isdigit()) or 0)))
            
            # Create ID ranges where possible
            if len(all_ids) > 1:
                best_element['id'] = f"{all_ids[0]}-{all_ids[-1]}"
            else:
                best_element['id'] = all_ids[0]
                
            id_processed_elements.append(best_element)
        else:
            # Only one element with this ID
            id_processed_elements.append(id_elements[0])
    
    # Now group by normalized name for elements that might be the same but have different IDs
    name_groups = {}
    for element in id_processed_elements:
        norm_name = normalize_element_name(element['name'])
        
        # Skip certain elements that should not be grouped by name
        if norm_name in ['download', 'company', 'summary']:
            # These are common names that might refer to different elements
            # Add them directly to the result
            if norm_name not in name_groups:
                name_groups[norm_name] = []
            name_groups[norm_name].append(element)
            continue
            
        if norm_name not in name_groups:
            name_groups[norm_name] = []
        name_groups[norm_name].append(element)
    
    # Process each name group
    grouped_elements = []
    for norm_name, name_elements in name_groups.items():
        if len(name_elements) > 1 and norm_name not in ['download', 'company', 'summary']:
            # Multiple elements with the same normalized name
            # Group by ID prefix (C for cards, numeric for interactive elements)
            prefix_groups = {}
            for element in name_elements:
                element_id = element['id']
                # Extract prefix (C for cards, numeric for interactive elements)
                if '-' in element_id:
                    prefix = element_id.split('-', 1)[0][0] if element_id.split('-', 1)[0] else ''
                else:
                    prefix = element_id[0] if element_id else ''
                
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(element)
            
            # For each prefix group, select the most descriptive element
            for prefix, prefix_elements in prefix_groups.items():
                # Sort by description length (longer is more descriptive)
                prefix_elements.sort(key=lambda e: len(e.get('description', '')), reverse=True)
                best_element = prefix_elements[0]
                
                # If there are multiple elements with the same prefix, combine their IDs
                if len(prefix_elements) > 1:
                    all_ids = set()
                    for e in prefix_elements:
                        if '-' in e['id']:
                            parts = e['id'].split('-', 1)
                            if len(parts) == 2:
                                start, end = parts
                                all_ids.add(start)
                                all_ids.add(end)
                            else:
                                # If splitting doesn't result in exactly 2 parts, use the ID as is
                                all_ids.add(e['id'])
                                continue
                        else:
                            all_ids.add(e['id'])
                    
                    # Sort and create ranges
                    all_ids = sorted(all_ids, key=lambda x: (x[0] if x[0].isalpha() else '', 
                                                        int(''.join(c for c in x if c.isdigit()) or 0)))
                    
                    # Create ID ranges
                    if len(all_ids) > 1:
                        best_element['id'] = f"{all_ids[0]}-{all_ids[-1]}"
                    else:
                        best_element['id'] = all_ids[0]
                
                grouped_elements.append(best_element)
        else:
            # Only one element with this normalized name or special case
            grouped_elements.extend(name_elements)
    
    return grouped_elements

def normalize_test_case_id(test_id):
    """
    Normalize test case IDs to handle duplicates.
    
    Args:
        test_id (str): Test case ID
        
    Returns:
        str: Normalized test case ID
    """
    # Extract the numeric part of the ID
    match = re.search(r'TC(\d+)', test_id)
    if match:
        return f"TC{match.group(1)}"
    return test_id

def get_test_case_key(test_case):
    """
    Generate a unique key for a test case based on its name and content.
    
    Args:
        test_case (dict): Test case dictionary
        
    Returns:
        str: Unique key for the test case
    """
    # Use the test case name as the primary key
    # This ensures we don't lose test cases with the same ID but different names
    return test_case["name"].lower().strip()

def convert_element_to_description(element, index):
    """
    Convert a UI element to a normalized description string.
    
    Args:
        element (dict): UI element dictionary
        index (int): Index for numbering the element
        
    Returns:
        str: Normalized description string
    """
    # Extract element name and capitalize first letter
    element_name = element['name']
    element_name = element_name[0].upper() + element_name[1:] if element_name else ''
    
    # Get element ID
    element_id = element.get('id', '')
    
    # Get description and clean it
    element_desc = element.get('description', '')
    
    # Remove any [Interactive: Yes/No] text
    element_desc = re.sub(r'\[Interactive:.*?\]\n?', '', element_desc)
    
    # Clean up any bullet points or extra formatting
    element_desc = re.sub(r'\s*\*\s*\[.*?\]\s*-\s*', ' - ', element_desc)
    
    # Format as [ID] - [Name] : Description
    if element_desc:
        description = f"[{element_id}] - [{element_name}] : {element_desc}"
    else:
        description = f"[{element_id}] - [{element_name}]"
    
    # Clean up extra spaces
    description = re.sub(r'\s+', ' ', description).strip()
    
    return description

def calculate_coverage(ui_elements, test_cases):
    """
    Calculate the element coverage rate of test cases.
    
    Args:
        ui_elements (list): List of UI elements
        test_cases (list): List of test cases
        
    Returns:
        tuple: (coverage_rate, covered_elements, uncovered_elements)
    """
    # Normalize UI element names for comparison
    normalized_elements = {}
    for element in ui_elements:
        norm_name = normalize_element_name(element['name'])
        normalized_elements[norm_name] = element
    
    # Track which elements are covered by test cases
    covered_elements = set()
    element_to_test_cases = {}
    
    # Check each test case for covered elements
    for test_case in test_cases:
        # Get coverage element from test case
        coverage_element = test_case.get('coverage_element', '')
        if not coverage_element:
            # Try to extract from objective or procedure steps
            objective = test_case.get('objective', '')
            steps = test_case.get('procedure_steps', [])
            
            # Look for element references in objective
            element_refs = re.findall(r'\[.*?\](?:\s*-\s*\[.*?\])?', objective)
            if element_refs:
                coverage_element = element_refs[0]
            
            # If not found in objective, check procedure steps
            if not coverage_element and steps:
                for step in steps:
                    element_refs = re.findall(r'\[.*?\](?:\s*-\s*\[.*?\])?', step)
                    if element_refs:
                        coverage_element = element_refs[0]
                        break
        
        if coverage_element:
            # Normalize the coverage element name
            norm_coverage = normalize_for_comparison(coverage_element)
            
            # Check if this element matches any UI element
            for norm_name, element in normalized_elements.items():
                # Check if the normalized names match or if one contains the other
                if norm_coverage == norm_name or norm_coverage in norm_name or norm_name in norm_coverage:
                    covered_elements.add(norm_name)
                    
                    # Track which test cases cover this element
                    if norm_name not in element_to_test_cases:
                        element_to_test_cases[norm_name] = []
                    element_to_test_cases[norm_name].append(test_case['id'] + ' - ' + test_case['name'])
    
    # Calculate coverage rate
    total_elements = len(normalized_elements)
    covered_count = len(covered_elements)
    coverage_rate = covered_count / total_elements if total_elements > 0 else 0
    
    # Find uncovered elements
    uncovered_elements = []
    for norm_name, element in normalized_elements.items():
        if norm_name not in covered_elements:
            uncovered_elements.append(element)
    
    return coverage_rate, element_to_test_cases, uncovered_elements

def normalize_for_comparison(name):
    """
    Normalize element names for comparison, ignoring words like 'card', 'button', etc.
    
    Args:
        name (str): Element name
        
    Returns:
        str: Normalized element name for comparison
    """
    # Remove ID prefix if present (e.g., "[C0] - ")
    name = re.sub(r'^\[.*?\]\s*-\s*', '', name)
    
    # Remove brackets if present
    name = re.sub(r'[\[\]]', '', name)
    
    # Remove common suffixes
    name = re.sub(r'\s+(Button|Tab|Card|Element)s?$', '', name, flags=re.IGNORECASE)
    
    # Convert to lowercase for case-insensitive comparison
    return name.lower().strip()

def process_multiple_tasks(base_folder, task_id, output_file='parsed_results.json', test_response_file=None):
    """
    Process multiple interact_messages.json files across different task folders.
    
    Args:
        base_folder (str): Base folder containing task folders
        task_id (str): Task ID prefix to match
        output_file (str): Path to save the combined results
        test_response_file (str): Path to the test response file to update
        
    Returns:
        dict: Combined results
    """
    # Initialize combined results
    combined_results = {
        "ui_elements": [],
        "test_cases": []
    }
    
    # Find all task folders matching the task ID
    task_pattern = os.path.join(base_folder, f"{task_id}_TC*")
    task_folders = glob.glob(task_pattern)
    
    if not task_folders:
        print(f"No task folders found matching pattern: {task_pattern}")
        return combined_results
    
    # Initialize lists to collect all elements and test cases
    all_elements = []
    all_test_cases = []
    
    # Process each task folder
    for folder in sorted(task_folders):
        json_file = os.path.join(folder, "interact_messages.json")
        if os.path.exists(json_file):
            print(f"Processing: {json_file}")
            result = parse_interact_messages(json_file)
            
            # Debug output
            print(f"  Found {len(result['ui_elements'])} UI elements and {len(result['test_cases'])} test cases")
            if result['test_cases']:
                print(f"  Test cases: {', '.join([tc['id'] + ' - ' + tc['name'] for tc in result['test_cases']])}")
            else:
                print(f"  No test cases found in this file")
            
            # Collect all UI elements
            all_elements.extend(result["ui_elements"])
            
            # Collect all test cases
            all_test_cases.extend(result["test_cases"])
    
    # Group similar elements
    grouped_elements = group_similar_elements(all_elements)
    
    # Group test cases by name (which is more reliable than ID)
    test_case_groups = {}
    for test_case in all_test_cases:
        # Generate a unique key based on test case name
        test_key = get_test_case_key(test_case)
        if test_key not in test_case_groups:
            test_case_groups[test_key] = []
        test_case_groups[test_key].append(test_case)
    
    # Select the most detailed test case from each group
    unique_test_cases = []
    for test_key, test_cases in test_case_groups.items():
        # Sort by procedure steps length (more steps is more detailed)
        test_cases.sort(key=lambda tc: len(tc.get("procedure_steps", [])), reverse=True)
        unique_test_cases.append(test_cases[0])
    
    # Sort test cases by category and then by ID
    def get_test_case_category(tc):
        name = tc['name'].lower()
        if 'ui design' in name or 'style' in name:
            return 1  # UI Design tests
        elif 'report' in name or 'download' in name:
            return 2  # Report/Download tests
        elif 'company' in name or 'selector' in name:
            return 3  # Company selection tests
        elif 'data' in name or 'information' in name or 'stock' in name:
            return 4  # Data/Information tests
        else:
            return 5  # Other tests
    
    # Sort first by category, then by name
    unique_test_cases.sort(key=lambda tc: (get_test_case_category(tc), tc['name']))
    
    # Add all unique elements and test cases to the combined results
    combined_results["ui_elements"] = grouped_elements
    combined_results["test_cases"] = unique_test_cases
    
    # Calculate coverage rate
    coverage_rate, element_to_test_cases, uncovered_elements = calculate_coverage(grouped_elements, unique_test_cases)
    combined_results["coverage_rate"] = coverage_rate
    combined_results["uncovered_elements"] = [f"[{e['id']}] - [{e['name']}]" for e in uncovered_elements]
    
    # Save the combined results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, indent=2)
    
    # Print a summary of the parsed elements and test cases
    print(f"\nFound {len(combined_results['ui_elements'])} unique UI elements:")
    for element in combined_results['ui_elements']:
        interactive_str = "True" if element.get('interactive', False) else "False"
        print(f"  - [{element['id']}] - [{element['name']}] (Interactive: {interactive_str})")
    
    print(f"\nFound {len(combined_results['test_cases'])} unique test cases:")
    for test_case in combined_results['test_cases']:
        print(f"  - {test_case['id']} - {test_case['name']}")
    
    print(f"\nElement Coverage Rate: {coverage_rate:.2%}")
    if uncovered_elements:
        print("\nUncovered Elements:")
        for element in uncovered_elements:
            print(f"  - [{element['id']}] - [{element['name']}]")
    
    # If a test response file is specified, update it with the parsed results
    if test_response_file and os.path.exists(test_response_file):
        try:
            # Load the test response file
            with open(test_response_file, 'r', encoding='utf-8') as f:
                test_response = json.load(f)
            
            # Convert UI elements to descriptions with sequential numbering
            element_descriptions = [convert_element_to_description(element, i+1) for i, element in enumerate(grouped_elements)]
            
            # Add element_requirement to the test response
            test_response["element_requirement"] = element_descriptions
            
            # Categorize test cases
            functionality_tests = []
            data_display_tests = []
            design_validation_tests = []
            
            for test_case in unique_test_cases:
                # Convert procedure_steps to procedure if needed
                if 'procedure_steps' in test_case and 'procedure' not in test_case:
                    test_case['procedure'] = test_case['procedure_steps']
                    del test_case['procedure_steps']
                
                # Categorize the test case based on its name first, then type
                test_name = test_case.get('name', '').lower()
                test_type = test_case.get('type', '').lower()
                
                # Check if it's a UI design or style test based on name
                if 'ui design' in test_name or 'style' in test_name:
                    design_validation_tests.append(test_case)
                # Otherwise categorize based on type
                elif 'interaction' in test_type or 'interactive' in test_type:
                    functionality_tests.append(test_case)
                elif 'data' in test_type or 'display' in test_type:
                    data_display_tests.append(test_case)
                else:
                    # If no specific type or doesn't match the above, put in design validation
                    design_validation_tests.append(test_case)
            
            # Update the test cases in the test response
            if 'test_cases' not in test_response:
                test_response['test_cases'] = {}
            
            # Reindex test cases in each category and remove the type field
            def reindex_test_cases(test_cases):
                reindexed = []
                for i, test_case in enumerate(test_cases):
                    # Create a copy of the test case to avoid modifying the original
                    tc_copy = test_case.copy()
                    # Update the ID to be sequential starting from 1
                    tc_copy['id'] = f"TC{i+1:03d}"
                    # Remove the type field if it exists
                    if 'type' in tc_copy:
                        del tc_copy['type']
                    # Keep coverage_element field in the output
                    # if 'coverage_element' in tc_copy:
                    #     del tc_copy['coverage_element']
                    reindexed.append(tc_copy)
                return reindexed
            
            # Apply reindexing to each category
            test_response['test_cases']['functionality_testing'] = reindex_test_cases(functionality_tests)
            test_response['test_cases']['data_display_testing'] = reindex_test_cases(data_display_tests)
            test_response['test_cases']['design_validation_testing'] = reindex_test_cases(design_validation_tests)
            
            # Add coverage information
            test_response['coverage_rate'] = coverage_rate
            test_response['uncovered_elements'] = [f"[{e['id']}] - [{e['name']}]" for e in uncovered_elements]
            
            # Save the updated test response
            with open(test_response_file, 'w', encoding='utf-8') as f:
                json.dump(test_response, f, indent=2)
            
            print(f"\nTest response file updated: {test_response_file}")
            
        except Exception as e:
            print(f"Error updating test response file: {e}")
    
    print(f"\nResults saved to {output_file}")
    
    return combined_results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse interact_messages.json files')
    parser.add_argument('--file', dest='file_path', help='Path to a single interact_messages.json file')
    parser.add_argument('--task', dest='task_id', help='Task ID to process multiple folders (e.g., task000001-1)')
    parser.add_argument('--base-folder', dest='base_folder', help='Base folder containing task folders', default='tasks/results')
    parser.add_argument('--output', help='Path to save the parsed results', default='parsed_results.json')
    parser.add_argument('--test-response', dest='test_response_file', help='Path to the test response file to update')
    
    args = parser.parse_args()
    
    if args.file_path:
        # Process a single file
        result = parse_interact_messages(args.file_path)
        
        # Save the result
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print(f"Results saved to {args.output}")
        print(f"\nResults saved to {args.output}")
    elif args.task_id:
        # Process multiple task folders
        process_multiple_tasks(args.base_folder, args.task_id, args.output, args.test_response_file)
    else:
        print("Error: Either --file or --task argument must be provided.")
        parser.print_help()

if __name__ == "__main__":
    main()
