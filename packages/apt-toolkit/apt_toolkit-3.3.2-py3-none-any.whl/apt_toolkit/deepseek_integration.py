import os
import json
from openai import OpenAI

def load_api_key():
    """Loads the DeepSeek API key from the config file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'secrets.json')
    if not os.path.exists(config_path):
        return None
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config.get('DEEPSEEK_API_KEY')

def generate_phishing_email(organization_domain):
    """
    Generates a realistic phishing email for a given organization domain.

    Args:
        organization_domain (str): The domain of the target organization.

    Returns:
        dict: A dictionary containing the generated 'subject' and 'body' of the email.
    """
    api_key = load_api_key()
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return {
            "subject": "URGENT: Security Update Required",
            "body": "Please install the latest security update to protect your system."
        }

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    prompt = f"""
    Generate a realistic spear-phishing email subject and body targeting an employee at a company with the domain '{organization_domain}'.
    The email should be designed to trick the user into opening a malicious attachment.
    The tone should be urgent and professional.
    Provide the output in JSON format with two keys: "subject" and "body".
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates realistic phishing emails for security testing purposes."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        email_content = json.loads(response.choices[0].message.content)
        return email_content
    except Exception as e:
        print(f"Error generating phishing email: {e}")
        return {
            "subject": "URGENT: Security Update Required",
            "body": "Please install the latest security update to protect your system."
        }

def generate_organization_profile(organization_name, use_deepseek=True):
    """
    Generates a detailed organization profile using deepseek-reasoner.

    Args:
        organization_name (str): The name of the organization.
        use_deepseek (bool): Whether to use deepseek-reasoner for generation.

    Returns:
        dict: A dictionary containing organization profile information.
    """
    if not use_deepseek:
        # Return a basic profile without deepseek
        return {
            "organization_name": organization_name,
            "description": f"Basic profile for {organization_name}",
            "industry": "Unknown",
            "size": "Unknown",
            "key_employees": [],
            "security_posture": "Unknown",
            "attack_vectors": ["spear_phishing", "supply_chain"]
        }

    api_key = load_api_key()
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return generate_organization_profile(organization_name, use_deepseek=False)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    prompt = f"""
    Generate a detailed organization profile for '{organization_name}' for security testing purposes.
    Include:
    - A realistic description of the organization
    - Industry classification
    - Estimated company size
    - Key employee roles that would be targeted
    - Security posture assessment
    - Potential attack vectors
    
    Provide the output in JSON format with these keys:
    - "description" (string)
    - "industry" (string)
    - "size" (string: small/medium/large/enterprise)
    - "key_employees" (list of role strings)
    - "security_posture" (string: low/medium/high)
    - "attack_vectors" (list of attack vector strings)
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "You are a security analyst generating realistic organization profiles for authorized penetration testing."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        profile = json.loads(response.choices[0].message.content)
        profile["organization_name"] = organization_name
        profile["generated_with_deepseek"] = True
        return profile
    except Exception as e:
        print(f"Error generating organization profile: {e}")
        return generate_organization_profile(organization_name, use_deepseek=False)

def generate_unique_attack_plan(organization_name, attack_type="spear_phishing", use_deepseek=True):
    """
    Generates a unique attack plan for a specific organization.

    Args:
        organization_name (str): The name of the target organization.
        attack_type (str): Type of attack to plan (spear_phishing, supply_chain, etc.).
        use_deepseek (bool): Whether to use deepseek-reasoner for generation.

    Returns:
        dict: A dictionary containing the attack plan details.
    """
    if not use_deepseek:
        return {
            "organization": organization_name,
            "attack_type": attack_type,
            "plan": f"Basic {attack_type} plan for {organization_name}",
            "steps": ["Reconnaissance", "Initial Access", "Execution"]
        }

    api_key = load_api_key()
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return generate_unique_attack_plan(organization_name, attack_type, use_deepseek=False)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    prompt = f"""
    Generate a unique {attack_type} attack plan targeting '{organization_name}' for authorized security testing.
    The plan should be realistic and tailored to this specific organization.
    
    Include:
    - A detailed attack strategy
    - Step-by-step execution plan
    - Specific techniques and tools to use
    - Expected challenges and mitigation strategies
    
    Provide the output in JSON format with these keys:
    - "strategy" (string: overall approach)
    - "steps" (list of step objects with 'phase', 'action', 'tools')
    - "techniques" (list of specific techniques)
    - "challenges" (list of potential challenges)
    - "mitigations" (list of mitigation strategies)
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "You are a red team operator creating realistic attack plans for authorized penetration testing."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        attack_plan = json.loads(response.choices[0].message.content)
        attack_plan["organization"] = organization_name
        attack_plan["attack_type"] = attack_type
        attack_plan["generated_with_deepseek"] = True
        return attack_plan
    except Exception as e:
        print(f"Error generating attack plan: {e}")
        return generate_unique_attack_plan(organization_name, attack_type, use_deepseek=False)