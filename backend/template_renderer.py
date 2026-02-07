"""Flexible template renderer for custom email templates."""
import re
from typing import Dict, Any


def render_custom_template(subject: str, body: str, data: Dict[str, Any]) -> Dict[str, str]:
    """
    Render custom template with variable substitution.
    
    Supports {{variable_name}} syntax. Replaces with actual values from data dict.
    Missing variables are replaced with empty string.
    
    Args:
        subject: Email subject template
        body: Email body template
        data: Dictionary with variable values
        
    Returns:
        Dict with 'subject' and 'body' keys containing rendered content
    """
    
    def replace_variable(match):
        """Replace a single variable match."""
        var_name = match.group(1).strip()
        return str(data.get(var_name, ''))
    
    # Pattern to match {{variable_name}}
    pattern = r'\{\{([^}]+)\}\}'
    
    # Replace variables in subject and body
    rendered_subject = re.sub(pattern, replace_variable, subject)
    rendered_body = re.sub(pattern, replace_variable, body)
    
    return {
        'subject': rendered_subject,
        'body': rendered_body
    }


def get_template_variables(text: str) -> list:
    """
    Extract all variables from a template string.
    
    Args:
        text: Template text containing {{variables}}
        
    Returns:
        List of variable names found in the template
    """
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, text)
    return [match.strip() for match in matches]


def validate_template(subject: str, body: str, available_columns: list) -> Dict[str, Any]:
    """
    Validate template against available columns.
    
    Args:
        subject: Email subject template
        body: Email body template
        available_columns: List of available column names from CSV
        
    Returns:
        Dict with 'valid' bool and 'missing_columns' list
    """
    # Get all variables used in templates
    subject_vars = get_template_variables(subject)
    body_vars = get_template_variables(body)
    all_vars = set(subject_vars + body_vars)
    
    # Check for missing columns
    available_set = set(available_columns)
    missing = [var for var in all_vars if var not in available_set]
    
    return {
        'valid': len(missing) == 0,
        'missing_columns': missing,
        'used_columns': list(all_vars)
    }
