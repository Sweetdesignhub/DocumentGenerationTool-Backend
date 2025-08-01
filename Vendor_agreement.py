import os
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime, timedelta
import re
from typing import Dict, Tuple

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class DocumentGenerator:
    def __init__(self):
        self.today = datetime.now().strftime("%B %d, %Y")
        self.one_year_later = (datetime.now() + timedelta(days=365)).strftime("%B %d, %Y")
        self.contract_id = f"CTR-{datetime.now().year}-{datetime.now().month:02d}{datetime.now().day:02d}"
        self.parsed_prompt = {}

    def _placeholder(self, label: str) -> str:
        """Generate consistent editable placeholder"""
        return f"[{label.upper()}]"

    def _call_groq(self, prompt: str) -> str:
        """Helper function to call Groq API with consistent parameters"""
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Lower temperature for more deterministic results
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()

    def _parse_user_prompt(self, user_prompt: str) -> Dict[str, str]:
        """Parse explicitly stated fields from user prompt; insert editable placeholders if absent."""
        # This is a simplified parser - you may want to enhance it based on your specific needs
        return {
        "buyer_name": self._extract_pattern(user_prompt, r"(?:buyer|purchaser)[: ]([A-Za-z0-9 &]+)") or self._placeholder("buyer name"),
        "supplier_name": self._extract_pattern(user_prompt, r"(?:supplier|vendor)[: ]([A-Za-z0-9 &]+)") or self._placeholder("supplier name"),
        "product": self._extract_pattern(user_prompt, r"(?:product|item|scope)[: ](.+?)(?=\n|,|\.|$)") or self._placeholder("product description"),
        "po_reference": self._extract_pattern(user_prompt, r"(?:PO|purchase order)[: ]?(#?\w+)") or self._placeholder("PO reference"),
        "price": self._extract_pattern(user_prompt, r"(?:price|amount|value)[: ]?(₹|\$|€)?(\d[\d,]*)") or self._placeholder("total value"),
        "payment_terms": self._extract_pattern(user_prompt, r"(?:payment terms|payment)[: ](.+?)(?=\n|,|\.|$)") or self._placeholder("payment terms"),
        "effective_date": self._extract_pattern(user_prompt, r"(?:effective date|start date)[: ](.+?)(?=\n|,|\.|$)") or self._placeholder("effective date"),
        "delivery": self._extract_pattern(user_prompt, r"(?:delivery|shipping)[: ](.+?)(?=\n|,|\.|$)") or self._placeholder("delivery schedule and address"),
        "quality_standards": self._extract_pattern(user_prompt, r"(?:quality standards|standards)[: ](.+?)(?=\n|,|\.|$)") or "ISO 22000 and FSSAI food safety standards"
        }

    def _extract_entity(self, text: str, entity_type: str) -> Tuple[str, str, str]:
        """Extract entity details (name, address, representative)"""
        pattern = rf"{entity_type}[: ](.+?)[,;](.+?)[,;](?:represented by|rep|by)?(.+?)(?=\n|\.|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return (match.group(1).strip(), match.group(2).strip(), match.group(3).strip())
        return ("", "", "")

    def _extract_pattern(self, text: str, pattern: str, default: str = "") -> str:
        """Helper to extract text using regex pattern"""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    # Block generation functions with strict rules
    def _generate_title_block(self) -> str:
        """Generate title block with strict formatting"""
        return (
            f"[TITLE BLOCK START]\n"
            f"Vendor Supply Agreement\n"
            f"[TITLE BLOCK END]"
        )

    # New function for generating Contract ID....
    def _generate_contract_id(self) -> str:
        """Generate just the contract details section"""
        return (
            f"[CONTRACT ID BLOCK START]\n"
            f"Contract ID: {self.contract_id}\n"
            f"Effective Date: {self.today}\n"
            f"End Date: {self.one_year_later}\n"  # Added missing newline
            f"[CONTRACT ID BLOCK END]\n"  # Fixed closing tag
        )
    
    def _generate_parties_intro(self) -> str:
        """Generate parties introduction with strict formatting"""
        return (
            "[PARTIES INTRO BLOCK START]\n"
            "This Agreement is made between:\n"
            "[PARTIES INTRO BLOCK END]"
        )

    def _generate_buyer_block(self) -> str:
        name = self.parsed_prompt.get("buyer_name", self._placeholder("buyer name"))
        address = self._placeholder("buyer address")
        rep = self._placeholder("buyer representative")
        return (
            f"[BUYER BLOCK START]\n"
            f"Buyer:\n"
            f"Enterprise Name: {name}\n"
            f"Address: {address}\n"
            f"Authorized Representative: {rep}\n"
            f"[BUYER BLOCK END]"
        )

    def _generate_supplier_block(self) -> str:
        name = self.parsed_prompt.get("supplier_name", self._placeholder("supplier name"))
        address = self._placeholder("supplier address")
        rep = self._placeholder("supplier representative")
        return (
            f"[SUPPLIER BLOCK START]\n"
            f"Supplier:\n"
            f"Vendor Name: {name}\n"
            f"Address: {address}\n"
            f"Authorized Representative: {rep}\n"
            f"[SUPPLIER BLOCK END]"
        )

    def _generate_scope_block(self) -> str:
        """Generate scope block with strict formatting"""
        product = self.parsed_prompt.get("product", "[PRODUCT DESCRIPTION]")
        po_ref = self.parsed_prompt.get("po_reference", "[PO REFERENCE]")
        return (
            f"[SCOPE BLOCK START]\n"
            f"1. Scope of Agreement\n"
            f"Supplier agrees to supply {product} as per the specifications and quantities "
            f"defined in PO-{po_ref}. Product must meet the food-grade quality standards "
            f"prescribed by FSSAI.\n"
            f"[SCOPE BLOCK END]"
        )

    def _generate_commercial_block(self) -> str:
        """Generate commercial terms with strict formatting"""
        price = self.parsed_prompt.get("price", "[TOTAL VALUE]")
        payment_terms = self.parsed_prompt.get("payment_terms", "[PAYMENT TERMS]")
        return (
            f"[COMMERCIAL BLOCK START]\n"
            f"2. Commercial Terms\n"
            f"Total Order Value: ₹{price}\n"
            f"Payment Terms: {payment_terms}\n"
            f"Price Validity: Fixed for the contract period\n"
            f"Taxes: Inclusive of GST (18%)\n"
            f"[COMMERCIAL BLOCK END]"
        )

    def _generate_delivery_block(self) -> str:
        """Generate delivery terms with strict formatting"""
        delivery_info = self.parsed_prompt.get("delivery", "[DELIVERY SCHEDULE AND ADDRESS]")
        return (
            f"[DELIVERY BLOCK START]\n"
            f"3. Delivery Terms\n"
            f"Delivery Schedule: {delivery_info}\n"
            f"Delivery Address: [SPECIFY DELIVERY ADDRESS]\n"
            f"Delivery Delays: Subject to penalty of ₹2,000 per day beyond 3-day grace period\n"
            f"[DELIVERY BLOCK END]"
        )

    def _generate_quality_block(self) -> str:
        """Generate quality assurance with strict formatting"""
        standards = self.parsed_prompt.get("quality_standards", "ISO 22000 and FSSAI food safety standards")
        return (
            f"[QUALITY BLOCK START]\n"
            f"4. Quality Assurance\n"
            f"Supplier must adhere to {standards}\n"
            f"Buyer reserves the right to conduct periodic inspections\n"
            f"Rejected material will be returned at supplier's cost within 7 days\n"
            f"[QUALITY BLOCK END]"
        )

    def _generate_penalties_block(self) -> str:
        """Generate penalties block with strict formatting"""
        return (
            f"[PENALTIES BLOCK START]\n"
            f"5. Penalties & Liabilities\n"
            f"Penalty Clause: 5% deduction for any batch with more than 2% foreign matter\n"
            f"Insurance: Supplier shall insure all shipments against transit damage\n"
            f"Indemnity: Supplier will indemnify the buyer against any third-party claims due to quality failure\n"
            f"[PENALTIES BLOCK END]"
        )

    def _generate_confidentiality_block(self) -> str:
        """Generate confidentiality block with strict formatting"""
        return (
            f"[CONFIDENTIALITY BLOCK START]\n"
            f"6. Confidentiality\n"
            f"Both parties agree to maintain the confidentiality of all business information\n"
            f"exchanged under this agreement and not disclose it to third parties without\n"
            f"prior written consent. This obligation survives termination of the agreement.\n"
            f"[CONFIDENTIALITY BLOCK END]"
        )

    def generate_agreement(self, user_prompt: str) -> Dict[str, str]:
        """
        Generate complete agreement from a single user prompt
        Returns structured blocks of the agreement with strict formatting
        """
        # First parse the user prompt to extract structured data
        self.parsed_prompt = self._parse_user_prompt(user_prompt)
        print("Parsed Prompt:", self.parsed_prompt)
        
        # Generate each block with its dedicated function
        generated_content = "\n\n".join([
            self._generate_title_block(),
            self._generate_contract_id(),
            self._generate_parties_intro(),
            self._generate_buyer_block(),
            self._generate_supplier_block(),
            self._generate_scope_block(),
            self._generate_commercial_block(),
            self._generate_delivery_block(),
            self._generate_quality_block(),
            self._generate_penalties_block(),
            self._generate_confidentiality_block()
        ])
        
        # Parse the generated content into structured blocks
        return self._parse_to_blocks(generated_content)

    def _parse_to_blocks(self, content: str) -> Dict[str, str]:
        """
        Parse generated content into structured blocks with validation
        """
        blocks = {
            'title': '',
            'contract_id':'',
            'parties_intro': '',
            'buyer': '',
            'supplier': '',
            'scope': '',
            'commercial': '',
            'delivery': '',
            'quality': '',
            'penalties': '',
            'confidentiality': ''
        }
        
        # Extract all blocks using regex
        block_pattern = re.compile(
            r'\[(.*?) BLOCK START\](.*?)\[.*? BLOCK END\]',
            re.DOTALL
        )
        
        found_blocks = block_pattern.findall(content)
        
        for block_type, block_content in found_blocks:
            block_key = block_type.lower().replace(" ", "_")
            if block_key in blocks:
                blocks[block_key] = block_content.strip()
        
        # Validate all required blocks are present
        for block_name in blocks:
            if not blocks[block_name]:
                raise ValueError(f"Missing required block: {block_name}")
                
        return blocks

    # Individual getter methods for each block
    def get_title_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('title', '')

    def get_contract_id(self, agreement: Dict[str, str]) -> str:
        return agreement.get('contract_id', '')
    
    def get_parties_intro(self, agreement: Dict[str, str]) -> str:
        return agreement.get('parties_intro', '')

    def get_buyer_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('buyer', '')

    def get_supplier_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('supplier', '')

    def get_scope_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('scope', '')

    def get_commercial_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('commercial', '')

    def get_delivery_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('delivery', '')

    def get_quality_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('quality', '')

    def get_penalties_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('penalties', '')

    def get_confidentiality_block(self, agreement: Dict[str, str]) -> str:
        return agreement.get('confidentiality', '')