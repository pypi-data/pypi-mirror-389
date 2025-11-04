"""
Runner for the Chinese National Security Campaign.
"""

import asyncio
from aiosmtpd.controller import Controller
from apt_toolkit.real_campaign_orchestrator import RealCampaignOrchestrator

class CampaignConfig:
    def __init__(self, port):
        self.target_email = "test@example.com"
        self.smtp_port = port

class MyHandler:
    async def handle_DATA(self, server, session, envelope):
        print('--- Begin message ---')
        print(envelope.content.decode('utf8', errors='replace'))
        print('--- End message ---')
        return '250 Message accepted for delivery'

def run_campaign():
    """
    Runs the full-chain campaign.
    """
    controller = Controller(MyHandler())
    controller.start()
    print(f"aiosmtpd server started on {controller.hostname}:{controller.port}")

    config = CampaignConfig(controller.port)
    orchestrator = RealCampaignOrchestrator(config)
    orchestrator.run_initial_access()
    orchestrator.run_persistence()
    orchestrator.run_privilege_escalation()

    controller.stop()

if __name__ == "__main__":
    run_campaign()

