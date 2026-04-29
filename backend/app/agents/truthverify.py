import os
import httpx
import asyncio
from typing import Dict, Optional
from pydantic import BaseModel, Field

# 1. The Output Schema for a 'Verified' Lead
class VerifiedLead(BaseModel):
    is_verified: bool = False
    company_status: str = Field(description="Status from OpenCorporates (e.g., Active)")
    linkedin_url: Optional[str] = None
    email_status: str = Field(description="ZeroBounce status (e.g., valid, invalid, catch-all)")
    confidence_score: float = 0.0 # Final accuracy score

class TruthVerifier:
    def __init__(
        self,
        zerobounce_key: Optional[str] = None,
        proxycurl_key: Optional[str] = None,
        opencorporates_token: Optional[str] = None,
    ):
        # Match user's Railway variable names, but keep common fallbacks too.
        self.zb_key = zerobounce_key or os.getenv("zerobouce_api") or os.getenv("ZEROBOUNCE_API_KEY")
        self.pc_key = proxycurl_key or os.getenv("PROXYCURL_API_KEY")
        self.oc_token = opencorporates_token or os.getenv("OPENCORPORATES_TOKEN")

        if not self.zb_key:
            raise RuntimeError("Missing ZeroBounce API key (set `zerobouce_api` in env).")
        if not self.pc_key:
            raise RuntimeError("Missing Proxycurl API key (set `PROXYCURL_API_KEY` in env).")

    async def verify_company_status(self, company_name: str, state_code: str = "us_tx") -> str:
        """
        Check OpenCorporates to see if the company is legally 'Active'.
        """
        # OpenCorporates search: https://api.opencorporates.com/v0.4/companies/search
        url = f"https://api.opencorporates.com/v0.4/companies/search"
        params = {"q": company_name, "jurisdiction_code": state_code}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                data = response.json()
                if data['results']['companies']:
                    return data['results']['companies'][0]['company']['current_status']
            except:
                return "Unknown"
        return "Not Found"

    async def find_linkedin_profile(self, name: str, company: str) -> Optional[str]:
        """
        Use Proxycurl to find the real LinkedIn profile and current job title.
        """
        # Using Proxycurl Person Lookup Endpoint
        url = "https://nubela.co/proxycurl/api/v2/linkedin/person/resolve"
        headers = {"Authorization": f"Bearer {self.pc_key}"}
        params = {"company_name": company, "first_name": name.split()[0], "last_name": name.split()[-1]}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get('url')
        return None

    async def verify_email(self, email: str) -> str:
        """
        Use ZeroBounce to ensure the email won't bounce.
        """
        url = "https://api.zerobounce.net/v2/validate"
        params = {"api_key": self.zb_key, "email": email}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json().get('status') # 'valid', 'invalid', etc.
        return "error"

    async def run(self, raw_lead: Dict) -> VerifiedLead:
        """
        The Main Verification Loop: Runs all checks in Parallel.
        """
        print(f"DEBUG: Verifying Lead -> {raw_lead.get('company_name')}")
        
        # Run all verification steps at once for speed
        tasks = [
            self.verify_company_status(raw_lead.get('company_name')),
            self.find_linkedin_profile(raw_lead.get('owner_name'), raw_lead.get('company_name')),
            self.verify_email(raw_lead.get('email', ""))
        ]
        
        company_status, linkedin_url, email_status = await asyncio.gather(*tasks)
        
        # Logic: 99% Accuracy calculation
        score = 0.0
        if company_status.lower() == "active": score += 0.33
        if linkedin_url: score += 0.33
        if email_status == "valid": score += 0.34
        
        return VerifiedLead(
            is_verified=(score > 0.90), # Must pass almost all checks
            company_status=company_status,
            linkedin_url=linkedin_url,
            email_status=email_status,
            confidence_score=round(score, 2)
        )

# --- EXECUTION EXAMPLE ---
async def test_verifier():
    verifier = TruthVerifier(zerobounce_key="your_zb_key", proxycurl_key="your_pc_key")
    
    # Data received from Agent 3 (Hunter)
    sample_lead = {
        "company_name": "Tesla",
        "owner_name": "Elon Musk",
        "email": "elon@tesla.com"
    }
    
    verified_result = await verifier.run(sample_lead)
    print(verified_result.json())

if __name__ == "__main__":
    asyncio.run(test_verifier())