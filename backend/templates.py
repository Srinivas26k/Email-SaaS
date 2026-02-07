"""Industry-specific email templates with variable substitution."""
from typing import Dict


# Template variable substitution helper
def render_template(industry: str, email_type: str, variables: Dict[str, str]) -> Dict[str, str]:
    """
    Render email template with variable substitution.
    
    Args:
        industry: Industry name (healthcare, fintech, edtech)
        email_type: Email type (initial, followup1, followup2)
        variables: Dictionary with variables for substitution
        
    Returns:
        Dict with 'subject' and 'body' keys
    """
    templates = {
        "healthcare": {
            "initial": {
                "subject": "Streamline Your Healthcare Operations with AI",
                "body": """Hi {{first_name}},

I noticed {{company}} is working in the healthcare space, and I wanted to reach out.

We help healthcare organizations automate their outreach and patient communication, saving 15+ hours per week while maintaining HIPAA compliance.

Would you be open to a 15-minute call to explore how we could help {{company}}?

Best regards,
Your Team"""
            },
            "followup1": {
                "subject": "Re: Streamline Your Healthcare Operations",
                "body": """Hi {{first_name}},

I wanted to follow up on my previous email about automating {{company}}'s patient outreach.

Our healthcare clients typically see:
• 40% increase in patient engagement
• 15+ hours saved per week
• Full HIPAA compliance

Would you have 15 minutes this week for a quick call?

Best,
Your Team"""
            },
            "followup2": {
                "subject": "Last follow-up: Healthcare automation for {{company}}",
                "body": """Hi {{first_name}},

This is my last follow-up. I understand you're busy, but I wanted to give you one more opportunity.

If healthcare automation isn't a priority right now, no worries. Feel free to reach out anytime if that changes.

Best of luck with {{company}}!

Best regards,
Your Team"""
            }
        },
        "fintech": {
            "initial": {
                "subject": "Scale Your Fintech Outreach Without the Headaches",
                "body": """Hi {{first_name}},

I came across {{company}} and was impressed by what you're building in fintech.

We help fintech companies automate their client outreach while maintaining compliance and personalization at scale.

Our clients typically close 30% more deals with 50% less manual work.

Would you be interested in a brief call to see if we could help {{company}}?

Best,
Your Team"""
            },
            "followup1": {
                "subject": "Re: Scale Your Fintech Outreach",
                "body": """Hi {{first_name}},

Following up on my email about automating {{company}}'s client outreach.

Quick question: Are you currently spending too much time on manual outreach tasks?

We've helped several fintech companies in your space automate their workflows while staying compliant.

Let me know if you'd like to see a quick demo.

Best regards,
Your Team"""
            },
            "followup2": {
                "subject": "Final note about {{company}}'s outreach automation",
                "body": """Hi {{first_name}},

I'll keep this brief – this is my final follow-up.

If outreach automation isn't on your radar right now, I totally understand. But if you'd ever like to explore how we could help {{company}} scale more efficiently, just reply to this email.

Wishing you continued success!

Best,
Your Team"""
            }
        },
        "edtech": {
            "initial": {
                "subject": "Help {{company}} Reach More Students Efficiently",
                "body": """Hi {{first_name}},

I noticed {{company}} is making waves in the edtech space!

We specialize in helping edtech companies automate their student and institution outreach, allowing you to focus on building great educational products.

Our clients see 3x more engagement with half the manual effort.

Would you be open to a quick 15-minute call to discuss how we could help {{company}}?

Cheers,
Your Team"""
            },
            "followup1": {
                "subject": "Re: Reach More Students at {{company}}",
                "body": """Hi {{first_name}},

Just wanted to circle back about automating {{company}}'s outreach to students and institutions.

Many edtech companies struggle with:
• Time-consuming manual outreach
• Low engagement rates
• Difficulty scaling personalization

We solve all three. Would you like to see how?

Best,
Your Team"""
            },
            "followup2": {
                "subject": "Last message about {{company}}'s outreach",
                "body": """Hi {{first_name}},

This will be my last email. I don't want to clutter your inbox!

If automating outreach becomes a priority for {{company}}, feel free to reach out anytime.

Keep doing great work in edtech!

Best regards,
Your Team"""
            }
        }
    }
    
    # Get template
    industry_lower = industry.lower()
    email_type_lower = email_type.lower()
    
    if industry_lower not in templates:
        raise ValueError(f"Unknown industry: {industry}")
    
    if email_type_lower not in templates[industry_lower]:
        raise ValueError(f"Unknown email type: {email_type}")
    
    template = templates[industry_lower][email_type_lower]
    
    # Substitute variables
    subject = template["subject"]
    body = template["body"]
    
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        subject = subject.replace(placeholder, str(value))
        body = body.replace(placeholder, str(value))
    
    return {
        "subject": subject,
        "body": body
    }
