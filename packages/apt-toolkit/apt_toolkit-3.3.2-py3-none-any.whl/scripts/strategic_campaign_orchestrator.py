import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from campaigns.financial_institution_campaign import run_campaign as financial_institution_campaign
from campaigns.do_and_private_sector_campaign import run_campaign as do_and_private_sector_campaign
from campaigns.apt41_campaign_enhanced import run_campaign as apt41_campaign_enhanced
from campaigns.accounting_firm_campaign import run_campaign as accounting_firm_campaign
from campaigns.energy_company_campaign import run_campaign as energy_company_campaign


def main():
    """
    Main function to orchestrate the strategic campaign.
    """
    print("[*] Starting strategic campaign...")

    print("\n[*] Kicking off financial institution campaign...")
    financial_institution_campaign.main()
    print("[*] Financial institution campaign finished.")

    print("\n[*] Kicking off do_and_private_sector_campaign...")
    do_and_private_sector_campaign.main()
    print("[*] do_and_private_sector_campaign finished.")

    print("\n[*] Kicking off apt41_campaign_enhanced...")
    apt41_campaign_enhanced.main()
    print("[*] apt41_campaign_enhanced finished.")

    print("\n[*] Kicking off accounting_firm_campaign...")
    accounting_firm_campaign.main()
    print("[*] accounting_firm_campaign finished.")

    print("\n[*] Kicking off energy_company_campaign...")
    energy_company_campaign.main()
    print("[*] energy_company_campaign finished.")

    print("\n[*] Strategic campaign finished.")


if __name__ == "__main__":
    main()
