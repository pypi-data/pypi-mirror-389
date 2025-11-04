#!/usr/bin/env python3
"""
Tests for the Advanced Payload Generation System
"""

import pytest
import os
import sys
import tempfile
import json
from pathlib import Path

# Add the payloads directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'payloads'))

from advanced_payload_generator import AdvancedPayloadGenerator
from evasion_techniques import EvasionTechniques
from campaign_payload_generator import CampaignPayloadGenerator

class TestAdvancedPayloadGenerator:
    """Test AdvancedPayloadGenerator class"""
    
    def test_initialization(self):
        """Test generator initialization"""
        generator = AdvancedPayloadGenerator()
        assert generator is not None
        assert hasattr(generator, 'evasion_techniques')
        assert len(generator.evasion_techniques) > 0
    
    def test_generate_random_string(self):
        """Test random string generation"""
        generator = AdvancedPayloadGenerator()
        random_str = generator.generate_random_string(10)
        assert len(random_str) == 10
        assert random_str.isalnum()
    
    def test_obfuscate_string(self):
        """Test string obfuscation"""
        generator = AdvancedPayloadGenerator()
        original = "test_string"
        obfuscated = generator.obfuscate_string(original)
        assert obfuscated != original
        assert len(obfuscated) > 0
    
    def test_generate_polymorphic_powershell(self):
        """Test polymorphic PowerShell generation"""
        generator = AdvancedPayloadGenerator()
        base_payload = "Write-Host 'Hello World'"
        polymorphic = generator.generate_polymorphic_powershell(base_payload)
        
        assert polymorphic is not None
        assert len(polymorphic) > len(base_payload)
        assert "Write-Host" in polymorphic or "Hello World" in polymorphic
    
    def test_generate_memory_execution_payload(self):
        """Test memory execution payload generation"""
        generator = AdvancedPayloadGenerator()
        payload = generator.generate_memory_execution_payload()
        
        assert payload is not None
        assert "VirtualAlloc" in payload or "CreateThread" in payload
        assert "Add-Type" in payload

class TestEvasionTechniques:
    """Test EvasionTechniques class"""
    
    def test_initialization(self):
        """Test evasion techniques initialization"""
        evasion = EvasionTechniques()
        assert evasion is not None
        assert hasattr(evasion, 'techniques')
        assert len(evasion.techniques) > 0
    
    def test_generate_random_name(self):
        """Test random name generation"""
        evasion = EvasionTechniques()
        name = evasion.generate_random_name(8)
        assert len(name) == 8
        assert name.isalpha()
    
    def test_encode_decode_string(self):
        """Test string encoding and decoding"""
        evasion = EvasionTechniques()
        original = "test_string"
        
        # Test base64
        encoded = evasion.encode_string(original, "base64")
        decoded = evasion.decode_string(encoded, "base64")
        assert decoded == original
        
        # Test hex
        encoded = evasion.encode_string(original, "hex")
        decoded = evasion.decode_string(encoded, "hex")
        assert decoded == original
    
    def test_generate_amsi_bypass(self):
        """Test AMSI bypass generation"""
        evasion = EvasionTechniques()
        bypass = evasion.generate_amsi_bypass("reflection")
        
        assert bypass is not None
        assert "AmsiUtils" in bypass or "amsiInitFailed" in bypass
    
    def test_get_evasion_profile(self):
        """Test evasion profile retrieval"""
        evasion = EvasionTechniques()
        profile = evasion.get_evasion_profile("stealth")
        
        assert profile is not None
        assert "description" in profile
        assert "techniques" in profile
        assert len(profile["techniques"]) > 0

class TestCampaignPayloadGenerator:
    """Test CampaignPayloadGenerator class"""
    
    def test_initialization(self):
        """Test campaign generator initialization"""
        generator = CampaignPayloadGenerator()
        assert generator is not None
        assert hasattr(generator, 'campaign_types')
        assert len(generator.campaign_types) > 0
    
    def test_generate_payload(self):
        """Test campaign payload generation"""
        generator = CampaignPayloadGenerator()
        payload_data = generator.generate_payload("Google", "technology_company")
        
        assert payload_data is not None
        assert "payload" in payload_data
        assert "metadata" in payload_data
        assert payload_data["metadata"]["organization"] == "Google"
        assert payload_data["metadata"]["campaign_type"] == "technology_company"
    
    def test_save_payload(self):
        """Test payload saving functionality"""
        generator = CampaignPayloadGenerator()
        payload_data = generator.generate_payload("TestOrg", "financial_institution")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = generator.save_payload(payload_data, temp_dir)
            
            assert os.path.exists(filepath)
            assert filepath.endswith('.ps1')
            
            # Verify file content
            with open(filepath, 'r') as f:
                content = f.read()
            assert len(content) > 0
            # Check for PowerShell-like content
            assert "$" in content or "Get-" in content

class TestIntegration:
    """Integration tests for the payload generation system"""
    
    def test_complete_payload_generation_flow(self):
        """Test complete payload generation flow"""
        campaign_generator = CampaignPayloadGenerator()
        
        # Generate payload for different scenarios
        test_cases = [
            ("Google", "technology_company"),
            ("Microsoft", "government_agency"),
            ("Apple", "financial_institution")
        ]
        
        for org, campaign_type in test_cases:
            payload_data = campaign_generator.generate_payload(org, campaign_type)
            
            # Verify payload structure
            assert "payload" in payload_data
            assert "metadata" in payload_data
            
            payload = payload_data["payload"]
            metadata = payload_data["metadata"]
            
            # Verify payload content
            assert len(payload) > 0
            # Check for PowerShell-like content
            assert "$" in payload or "Get-" in payload or "Amsi" in payload
            
            # Verify metadata
            assert metadata["organization"] == org
            assert metadata["campaign_type"] == campaign_type
            assert "payload_focus" in metadata
            assert "generated_at" in metadata
    
    def test_evasion_techniques_integration(self):
        """Test integration of evasion techniques"""
        evasion = EvasionTechniques()
        campaign_generator = CampaignPayloadGenerator()
        
        payload_data = campaign_generator.generate_payload("TestOrg", "government_agency")
        payload = payload_data["payload"]
        
        # Verify evasion techniques are applied
        assert "amsi" in payload.lower() or "bypass" in payload.lower()

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])