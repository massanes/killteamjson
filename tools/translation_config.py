#!/usr/bin/env python3
"""
Translation configuration - defines exactly which fields to translate for each JSON file.
"""

# Translation rules per file
TRANSLATION_RULES = {
    'actions.json': {
        'actions': {
            'name': True,
            'description': True,
            'effects': True,  # Array of strings
            'conditions': True,  # Array of strings
        }
    },
    
    'ops_2025.json': {
        'ops': {
            'title': True,
            'reveal': True,
            'additionalRules': True,
            'victoryPoints': True,
        },
        'actions': {
            'name': True,
            'description': True,
            'effects': True,  # Array of strings
            'conditions': True,  # Array of strings
        }
    },
    
    # Individual team files in teams/ subfolder (e.g., IMP-AOD.json)
    # Pattern: teams/*.json
    'teams': {
        # Root level fields
        'killteamName': True,
        'description': True,
        'composition': True,
        
        # Within opTypes array
        'opTypes': {
            'opTypeName': True,
            'weapons': {
                'wepName': True,
                'profiles': {
                    'profileName': True,
                }
            },
            'abilities': {
                'abilityName': True,
                'description': True,
            },
            'options': {
                'optionName': True,
                'description': True,
            }
        }
    },
    
    'universal_equipment.json': {
        'equipments': {
            'eqName': True,
            'description': True,
            'effects': True,
        },
        'actions': {
            'name': True,
            'description': True,
            'effects': True,  # Array of strings
            'conditions': True,  # Array of strings
        }
    },
    
    'weapon_rules.json': {
        'weapon_rules': {
            'name': True,
            'description': True,
        }
    }
}

def should_translate_field(file_name: str, field_path: list, field_name: str) -> bool:
    """
    Check if a field should be translated based on the file and field path.
    
    Args:
        file_name: Name of the JSON file (e.g., 'teams.json' or 'IMP-AOD.json')
        field_path: List of parent field names leading to this field (e.g., ['opTypes', 'weapons'])
                   Note: Arrays are represented by their field name, not array indices
        field_name: Name of the current field to check
    
    Returns:
        True if the field should be translated, False otherwise
    """
    # Check if this is a team file in the teams/ subfolder
    if file_name.endswith('.json') and 'teams' in file_name.lower():
        # Use 'teams' rules for any file in teams/ subfolder
        rules_key = 'teams'
    else:
        rules_key = file_name
    
    if rules_key not in TRANSLATION_RULES:
        return False
    
    rules = TRANSLATION_RULES[rules_key]
    
    # Navigate through the field path
    current_rules = rules
    for parent_field in field_path:
        if isinstance(current_rules, dict) and parent_field in current_rules:
            current_rules = current_rules[parent_field]
        else:
            # Path doesn't match rules, don't translate
            return False
    
    # Check if the field name is in the current rules
    if isinstance(current_rules, dict):
        return current_rules.get(field_name, False)
    
    return False

def get_translatable_fields_for_file(file_name: str) -> dict:
    """Get the translation rules for a specific file."""
    return TRANSLATION_RULES.get(file_name, {})

