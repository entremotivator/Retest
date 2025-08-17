
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from typing import Optional, Dict, Any, List

# Hardcoded URLs
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1BWz_FnYdzZyyl4WafSgoZV9rLHC91XOjstDcgwn_k6Y/edit?usp="
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/real-estate-address"  # Replace with actual webhook URL

# Configure page
st.set_page_config(
    page_title="Real Estate Management System",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for light blue theme
st.markdown("""
<style>
    .main {
        background-color: #f0f8ff;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #e6f3ff;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #b3d9ff;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .property-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    .property-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .property-card h4 {
        color: #2c3e50;
        margin-bottom: 1rem;
        font-size: 1.1em;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .property-card p {
        margin: 0.5rem 0;
        color: #555;
        font-size: 0.9em;
    }
    .selected-property {
        border: 3px solid #27ae60 !important;
        background: linear-gradient(135deg, #d5f4e6 0%, #ffffff 100%) !important;
    }
    .selection-indicator {
        background-color: #27ae60;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2980b9 0%, #1f5f8b 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .info-banner {
        background: linear-gradient(135deg, #e8f4fd 0%, #d6eaff 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
    }
    .success-banner {
        background: linear-gradient(135deg, #d5f4e6 0%, #c8e6c9 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #27ae60;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets Helper Class
class GoogleSheetsManager:
    """Helper class to manage Google Sheets operations"""
    
    def __init__(self, credentials_dict: Dict[str, Any]):
        """Initialize with service account credentials"""
        self.credentials_dict = credentials_dict
        self.client = None
        self.sheet = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                self.credentials_dict, scope
            )
            self.client = gspread.authorize(creds)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def connect_to_sheet(self, sheet_id: str, worksheet_name: str = None) -> bool:
        """Connect to a specific Google Sheet"""
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            if worksheet_name:
                self.sheet = spreadsheet.worksheet(worksheet_name)
            else:
                self.sheet = spreadsheet.sheet1
            return True
        except Exception as e:
            st.error(f"Failed to connect to sheet: {str(e)}")
            return False
    
    def get_all_data(self) -> Optional[pd.DataFrame]:
        """Get all data from the connected sheet"""
        try:
            if not self.sheet:
                raise Exception("No sheet connected")
            
            records = self.sheet.get_all_records()
            if records:
                df = pd.DataFrame(records)
                # Clean up empty rows
                df = df.dropna(how='all')
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return None
    
    def append_row(self, data: List[Any]) -> bool:
        """Append a row to the sheet"""
        try:
            if not self.sheet:
                raise Exception("No sheet connected")
            
            self.sheet.append_row(data)
            return True
        except Exception as e:
            st.error(f"Error appending row: {str(e)}")
            return False
    
    def update_cell(self, row: int, col: int, value: Any) -> bool:
        """Update a specific cell"""
        try:
            if not self.sheet:
                raise Exception("No sheet connected")
            
            self.sheet.update_cell(row, col, value)
            return True
        except Exception as e:
            st.error(f"Error updating cell: {str(e)}")
            return False
    
    def get_sheet_info(self) -> Dict[str, Any]:
        """Get information about the connected sheet"""
        try:
            if not self.sheet:
                return {}
            
            return {
                'title': self.sheet.title,
                'row_count': self.sheet.row_count,
                'col_count': self.sheet.col_count,
                'url': self.sheet.spreadsheet.url
            }
        except Exception as e:
            st.error(f"Error getting sheet info: {str(e)}")
            return {}
    
    def search_data(self, df: pd.DataFrame, search_term: str, columns: List[str] = None) -> pd.DataFrame:
        """Search data in the dataframe"""
        if df.empty or not search_term:
            return df
        
        if columns is None:
            columns = df.columns.tolist()
        
        # Create search mask
        mask = pd.Series([False] * len(df))
        
        for col in columns:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(
                    search_term, case=False, na=False
                )
        
        return df[mask]
    
    def filter_by_property_type(self, df: pd.DataFrame, property_type: str) -> pd.DataFrame:
        """Filter dataframe by property type"""
        if df.empty or property_type == "All":
            return df
        
        if 'propertyType' in df.columns:
            return df[df['propertyType'] == property_type]
        
        return df
    
    def sort_data(self, df: pd.DataFrame, sort_column: str, ascending: bool = True) -> pd.DataFrame:
        """Sort dataframe by specified column"""
        if df.empty or sort_column not in df.columns:
            return df
        
        return df.sort_values(by=sort_column, ascending=ascending)

def get_sheet_manager() -> Optional[GoogleSheetsManager]:
    """Get Google Sheets manager from session state"""
    if 'credentials' not in st.session_state:
        return None
    
    try:
        if 'sheets_manager' not in st.session_state:
            st.session_state['sheets_manager'] = GoogleSheetsManager(
                st.session_state['credentials']
            )
        return st.session_state['sheets_manager']
    except Exception as e:
        st.error(f"Failed to create sheets manager: {str(e)}")
        return None

def validate_credentials(credentials_dict: Dict[str, Any]) -> bool:
    """Validate Google service account credentials"""
    required_fields = [
        'type', 'project_id', 'private_key_id', 'private_key',
        'client_email', 'client_id', 'auth_uri', 'token_uri'
    ]
    
    for field in required_fields:
        if field not in credentials_dict:
            return False
    
    return credentials_dict.get('type') == 'service_account'

# Webhook Helper Class
class WebhookManager:
    """Helper class to manage webhook operations"""
    
    def __init__(self, webhook_url: str):
        """Initialize with webhook URL"""
        self.webhook_url = webhook_url
        self.timeout = 30  # seconds
        self.max_retries = 3
    
    def send_address_data(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send address data to n8n webhook with retry logic"""
        
        # Add metadata
        payload = {
            **address_data,
            "timestamp": datetime.now().isoformat(),
            "source": "streamlit_app",
            "version": "1.0"
        }
        
        # Attempt to send with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'RealEstate-Streamlit-App/1.0'
                    },
                    timeout=self.timeout
                )
                
                result = {
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'response_text': response.text,
                    'attempt': attempt + 1,
                    'payload': payload
                }
                
                if result['success']:
                    return result
                else:
                    st.warning(f"Attempt {attempt + 1} failed with status code: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.warning(f"Attempt {attempt + 1} timed out after {self.timeout} seconds")
            except requests.exceptions.ConnectionError:
                st.warning(f"Attempt {attempt + 1} failed: Connection error")
            except requests.exceptions.RequestException as e:
                st.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # All attempts failed
        return {
            'success': False,
            'status_code': None,
            'response_text': 'All retry attempts failed',
            'attempt': self.max_retries,
            'payload': payload
        }
    
    def validate_address_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate address data before sending"""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ['addressLine1', 'city', 'state', 'zipCode']
        for field in required_fields:
            if not data.get(field, '').strip():
                errors.append(f"Missing required field: {field}")
        
        # Optional but recommended fields
        recommended_fields = ['propertyType', 'county']
        for field in recommended_fields:
            if not data.get(field, '').strip():
                warnings.append(f"Missing recommended field: {field}")
        
        # Validate ZIP code format (basic validation)
        zip_code = data.get('zipCode', '').strip()
        if zip_code and not (zip_code.isdigit() and len(zip_code) == 5):
            if not (len(zip_code) == 10 and zip_code[5] == '-' and 
                   zip_code[:5].isdigit() and zip_code[6:].isdigit()):
                warnings.append("ZIP code format may be invalid (expected: 12345 or 12345-6789)")
        
        # Validate state (basic validation - should be 2 characters)
        state = data.get('state', '').strip()
        if state and len(state) != 2:
            warnings.append("State should be 2-character abbreviation (e.g., CA, NY)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def format_address_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and clean address data"""
        
        # Clean and format the data
        formatted_data = {}
        
        # Required fields
        formatted_data['addressLine1'] = form_data.get('addressLine1', '').strip()
        formatted_data['city'] = form_data.get('city', '').strip().title()
        formatted_data['state'] = form_data.get('state', '').strip().upper()
        formatted_data['zipCode'] = form_data.get('zipCode', '').strip()
        
        # Optional fields
        formatted_data['addressLine2'] = form_data.get('addressLine2', '').strip()
        formatted_data['county'] = form_data.get('county', '').strip().title()
        formatted_data['propertyType'] = form_data.get('propertyType', '').strip()
        formatted_data['notes'] = form_data.get('notes', '').strip()
        
        # Generate formatted address
        address_parts = [formatted_data['addressLine1']]
        if formatted_data['addressLine2']:
            address_parts.append(formatted_data['addressLine2'])
        address_parts.extend([
            formatted_data['city'],
            f"{formatted_data['state']} {formatted_data['zipCode']}"
        ])
        formatted_data['formattedAddress'] = ', '.join(filter(None, address_parts))
        
        return formatted_data
    
    def test_webhook_connection(self) -> Dict[str, Any]:
        """Test webhook connection with a ping"""
        test_payload = {
            "test": True,
            "message": "Connection test from Streamlit app",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'response_text': response.text[:200]  # First 200 chars
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': None
            }

def create_webhook_manager(webhook_url: str) -> WebhookManager:
    """Create and return a webhook manager instance"""
    return WebhookManager(webhook_url)

def display_webhook_result(result: Dict[str, Any]):
    """Display webhook result in Streamlit UI"""
    if result['success']:
        st.success("✅ Address submitted successfully to n8n webhook!")
        
        with st.expander("📋 Submission Details"):
            st.json({
                'status_code': result['status_code'],
                'attempt': result['attempt'],
                'timestamp': result['payload']['timestamp']
            })
            
        with st.expander("📤 Sent Data"):
            # Remove sensitive data for display
            display_payload = result['payload'].copy()
            st.json(display_payload)
            
    else:
        st.error("❌ Failed to submit address to webhook")
        
        with st.expander("🔍 Error Details"):
            st.write(f"**Status Code:** {result.get('status_code', 'N/A')}")
            st.write(f"**Attempts Made:** {result['attempt']}")
            st.write(f"**Error Message:** {result['response_text']}")
            
        st.info("💡 **Troubleshooting Tips:**")
        st.write("- Check if the n8n webhook URL is correct and accessible")
        st.write("- Verify that the n8n workflow is active")
        st.write("- Check your internet connection")
        st.write("- Contact your system administrator if the issue persists")

def validate_webhook_url(url: str) -> bool:
    """Basic validation of webhook URL format"""
    if not url:
        return False
    
    # Basic URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    # Should contain 'webhook' in the path (common for n8n)
    if 'webhook' not in url.lower():
        return False
    
    return True

# Report Generator Class
class ReportGenerator:
    """Helper class to generate various types of real estate reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for PDF generation"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#2c3e50')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e'),
            borderWidth=1,
            borderColor=colors.HexColor('#3498db'),
            leftIndent=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=10
        ))
    
    def calculate_investment_metrics(self, property_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive investment metrics"""
        
        # Extract values with defaults
        price = property_data.get("price", 0)
        noi = property_data.get("noi", 0)
        cash_invested = property_data.get("cash_invested", 0)
        gross_rental_income = property_data.get("gross_rental_income", 0)
        operating_expenses = property_data.get("operating_expenses", 0)
        total_debt_service = property_data.get("total_debt_service", 0)
        occupied_units = property_data.get("occupied_units", 0)
        total_units = property_data.get("total_units", 1)
        square_footage = property_data.get("square_footage", 1)
        property_taxes = property_data.get("property_taxes", 0)
        
        # Calculate derived values
        annual_cash_flow = gross_rental_income - operating_expenses - total_debt_service
        
        # Calculate metrics with safe division
        metrics = {
            "annual_cash_flow": annual_cash_flow,
            "cash_on_cash_return": (annual_cash_flow / cash_invested * 100) if cash_invested > 0 else 0,
            "cap_rate": (noi / price * 100) if price > 0 else 0,
            "dscr": (noi / total_debt_service) if total_debt_service > 0 else float('inf'),
            "gross_rental_yield": (gross_rental_income / price * 100) if price > 0 else 0,
            "price_per_sqft": (price / square_footage) if square_footage > 0 else 0,
            "oer": (operating_expenses / gross_rental_income * 100) if gross_rental_income > 0 else 0,
            "roi": (annual_cash_flow / cash_invested * 100) if cash_invested > 0 else 0,
            "occupancy_rate": (occupied_units / total_units * 100) if total_units > 0 else 0,
            "net_yield": ((annual_cash_flow + total_debt_service) / price * 100) if price > 0 else 0,
            "break_even_ratio": ((operating_expenses + total_debt_service) / gross_rental_income * 100) if gross_rental_income > 0 else 0
        }
        
        return metrics
    
    def _generate_investment_analysis(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Generate investment analysis and recommendations"""
        analysis = {
            "score": 0,
            "summary": [],
            "recommendations": [],
            "warnings": [],
            "risks": []
        }
        
        # Score and Analysis based on metrics
        if metrics["cash_on_cash_return"] >= 12: analysis["score"] += 20; analysis["summary"].append("Excellent Cash-on-Cash Return.")
        elif metrics["cash_on_cash_return"] >= 8: analysis["score"] += 15; analysis["summary"].append("Good Cash-on-Cash Return.")
        elif metrics["cash_on_cash_return"] >= 5: analysis["score"] += 10; analysis["warnings"].append("Cash-on-Cash Return is fair, consider optimizing expenses or increasing income.")
        else: analysis["score"] += 5; analysis["risks"].append("Low Cash-on-Cash Return, indicating poor cash flow generation relative to investment.")
        
        if metrics["cap_rate"] >= 8: analysis["score"] += 20; analysis["summary"].append("Strong Cap Rate, indicating good return potential.")
        elif metrics["cap_rate"] >= 6: analysis["score"] += 15; analysis["summary"].append("Good Cap Rate.")
        elif metrics["cap_rate"] >= 4: analysis["score"] += 10; analysis["warnings"].append("Cap Rate is fair, may indicate lower market demand or higher risk.")
        else: analysis["score"] += 5; analysis["risks"].append("Low Cap Rate, suggesting higher price relative to NOI.")
        
        if metrics["dscr"] >= 1.5: analysis["score"] += 20; analysis["summary"].append("Very strong Debt Service Coverage Ratio, excellent loan repayment ability.")
        elif metrics["dscr"] >= 1.25: analysis["score"] += 15; analysis["summary"].append("Healthy Debt Service Coverage Ratio.")
        elif metrics["dscr"] >= 1.0: analysis["score"] += 10; analysis["warnings"].append("DSCR is at break-even, monitor cash flow closely.")
        else: analysis["score"] += 5; analysis["risks"].append("DSCR below 1.0, indicating potential difficulty in covering debt payments.")
        
        if metrics["occupancy_rate"] >= 90: analysis["score"] += 15; analysis["summary"].append("High Occupancy Rate, stable rental income.")
        elif metrics["occupancy_rate"] >= 70: analysis["score"] += 10; analysis["warnings"].append("Moderate Occupancy Rate, potential for improvement.")
        else: analysis["score"] += 5; analysis["risks"].append("Low Occupancy Rate, impacting rental income and profitability.")
        
        if metrics["oer"] <= 35: analysis["score"] += 15; analysis["summary"].append("Low Operating Expense Ratio, efficient management.")
        elif metrics["oer"] <= 50: analysis["score"] += 10; analysis["warnings"].append("Moderate Operating Expense Ratio, review for potential savings.")
        else: analysis["score"] += 5; analysis["risks"].append("High Operating Expense Ratio, significantly impacting profitability.")
        
        # Recommendations
        if analysis["score"] >= 80: analysis["recommendations"].append("This property shows strong investment potential. Consider proceeding with due diligence.")
        elif analysis["score"] >= 60: analysis["recommendations"].append("Good investment opportunity, but further analysis on identified warnings is recommended.")
        else: analysis["recommendations"].append("This property carries significant risks. Thorough due diligence and risk mitigation strategies are essential before investment.")
        
        return analysis
    
    def generate_html_report(self, property_data: Dict[str, Any], metrics: Dict[str, float]) -> str:
        """Generate comprehensive HTML report"""
        
        report_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        # Investment analysis based on metrics
        analysis = self._generate_investment_analysis(metrics)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Real Estate Investment Analysis Report</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
                    color: #333;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #3498db;
                }}
                h1 {{ 
                    color: #2c3e50;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                }}
                .subtitle {{
                    color: #7f8c8d;
                    font-size: 1.1em;
                    margin-bottom: 20px;
                }}
                h2 {{ 
                    color: #34495e;
                    border-left: 5px solid #3498db;
                    padding-left: 15px;
                    margin-top: 40px;
                    margin-bottom: 20px;
                    font-size: 1.8em;
                }}
                .property-overview {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                .info-card {{
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 4px solid #3498db;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .info-card h3 {{
                    margin: 0 0 10px 0;
                    color: #2c3e50;
                    font-size: 1.1em;
                }}
                .info-card p {{
                    margin: 0;
                    font-size: 1.3em;
                    font-weight: bold;
                    color: #3498db;
                }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 20px 0;
                    background-color: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                th, td {{ 
                    padding: 15px; 
                    text-align: left; 
                    border-bottom: 1px solid #ecf0f1;
                }}
                th {{ 
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                tr:hover {{
                    background-color: #e8f4fd;
                    transition: background-color 0.3s ease;
                }}
                .metric-value {{
                    font-weight: bold;
                    font-size: 1.1em;
                }}
                .positive {{ color: #27ae60; }}
                .negative {{ color: #e74c3c; }}
                .neutral {{ color: #f39c12; }}
                .analysis-section {{
                    background: linear-gradient(135deg, #e8f4fd 0%, #d6eaff 100%);
                    padding: 25px;
                    border-radius: 10px;
                    margin: 30px 0;
                    border: 1px solid #3498db;
                }}
                .analysis-section h3 {{
                    color: #2c3e50;
                    margin-top: 0;
                }}
                .recommendation {{
                    background-color: #d5f4e6;
                    border-left: 4px solid #27ae60;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }}
                .warning {{
                    background-color: #ffeaa7;
                    border-left: 4px solid #f39c12;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }}
                .risk {{
                    background-color: #ffcccb;
                    border-left: 4px solid #e74c3c;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }}
                .footer {{
                    margin-top: 50px;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 0.9em;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                }}
                @media print {{
                    body {{ background: white; }}
                    .container {{ box-shadow: none; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 Real Estate Investment Analysis</h1>
                    <div class="subtitle">Comprehensive Property Investment Report</div>
                    <p><strong>Report Generated:</strong> {report_date}</p>
                </div>
                
                <h2>🏠 Property Overview</h2>
                <div class="property-overview">
                    <div class="info-card">
                        <h3>📍 Address</h3>
                        <p>{property_data.get('address', 'N/A')}</p>
                    </div>
                    <div class="info-card">
                        <h3>💰 Purchase Price</h3>
                        <p>${property_data.get('price', 0):,.2f}</p>
                    </div>
                    <div class="info-card">
                        <h3>📐 Square Footage</h3>
                        <p>{property_data.get('square_footage', 0):,} sq ft</p>
                    </div>
                    <div class="info-card">
                        <h3>🏘️ Property Type</h3>
                        <p>{property_data.get('property_type', 'N/A')}</p>
                    </div>
                    <div class="info-card">
                        <h3>🛏️ Bedrooms</h3>
                        <p>{property_data.get('bedrooms', 0)}</p>
                    </div>
                    <div class="info-card">
                        <h3>🚿 Bathrooms</h3>
                        <p>{property_data.get('bathrooms', 0)}</p>
                    </div>
                    <div class="info-card">
                        <h3>📅 Year Built</h3>
                        <p>{property_data.get('year_built', 'N/A')}</p>
                    </div>
                    <div class="info-card">
                        <h3>🏞️ Lot Size</h3>
                        <p>{property_data.get('lot_size', 0):,.0f} sq ft</p>
                    </div>
                </div>
                
                <h2>💰 Financial Summary</h2>
                <div class="property-overview">
                    <div class="info-card">
                        <h3>💵 Net Operating Income</h3>
                        <p>${property_data.get('noi', 0):,.2f}</p>
                    </div>
                    <div class="info-card">
                        <h3>💸 Cash Invested</h3>
                        <p>${property_data.get('cash_invested', 0):,.2f}</p>
                    </div>
                    <div class="info-card">
                        <h3>📈 Gross Rental Income</h3>
                        <p>${property_data.get('gross_rental_income', 0):,.2f}</p>
                    </div>
                    <div class="info-card">
                        <h3>📉 Operating Expenses</h3>
                        <p>${property_data.get('operating_expenses', 0):,.2f}</p>
                    </div>
                </div>
                
                <h2>📊 Investment Metrics</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                            <th>Industry Benchmark</th>
                            <th>Assessment</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Annual Cash Flow</td>
                            <td class="metric-value">${metrics['annual_cash_flow']:,.2f}</td>
                            <td>Positive</td>
                            <td class="{'positive' if metrics['annual_cash_flow'] > 0 else 'negative'}">
                                {'Excellent' if metrics['annual_cash_flow'] > 0 else 'Needs Improvement'}
                            </td>
                        </tr>
                        <tr>
                            <td>Cash-on-Cash Return</td>
                            <td class="metric-value">{metrics['cash_on_cash_return']:.2f}%</td>
                            <td>8-12%</td>
                            <td class="{'positive' if metrics['cash_on_cash_return'] >= 8 else 'negative' if metrics['cash_on_cash_return'] < 5 else 'neutral'}">
                                {'Excellent' if metrics['cash_on_cash_return'] >= 12 else 'Good' if metrics['cash_on_cash_return'] >= 8 else 'Fair' if metrics['cash_on_cash_return'] >= 5 else 'Poor'}
                            </td>
                        </tr>
                        <tr>
                            <td>Cap Rate</td>
                            <td class="metric-value">{metrics['cap_rate']:.2f}%</td>
                            <td>6-10%</td>
                            <td class="{'positive' if metrics['cap_rate'] >= 6 else 'negative' if metrics['cap_rate'] < 4 else 'neutral'}">
                                {'Excellent' if metrics['cap_rate'] >= 8 else 'Good' if metrics['cap_rate'] >= 6 else 'Fair' if metrics['cap_rate'] >= 4 else 'Poor'}
                            </td>
                        </tr>
                        <tr>
                            <td>Debt Service Coverage Ratio</td>
                            <td class="metric-value">{metrics['dscr']:.2f}</td>
                            <td>1.25+</td>
                            <td class="{'positive' if metrics['dscr'] >= 1.25 else 'negative' if metrics['dscr'] < 1.0 else 'neutral'}">
                                {'Excellent' if metrics['dscr'] >= 1.5 else 'Good' if metrics['dscr'] >= 1.25 else 'Fair' if metrics['dscr'] >= 1.0 else 'Poor'}
                            </td>
                        </tr>
                        <tr>
                            <td>Gross Rental Yield</td>
                            <td class="metric-value">{metrics['gross_rental_yield']:.2f}%</td>
                            <td>8-12%</td>
                            <td class="{'positive' if metrics['gross_rental_yield'] >= 8 else 'negative' if metrics['gross_rental_yield'] < 6 else 'neutral'}">
                                {'Excellent' if metrics['gross_rental_yield'] >= 10 else 'Good' if metrics['gross_rental_yield'] >= 8 else 'Fair' if metrics['gross_rental_yield'] >= 6 else 'Poor'}
                            </td>
                        </tr>
                        <tr>
                            <td>Price per Square Foot</td>
                            <td class="metric-value">${metrics['price_per_sqft']:.2f}</td>
                            <td>Market Dependent</td>
                            <td class="neutral">Market Analysis Required</td>
                        </tr>
                        <tr>
                            <td>Operating Expense Ratio (OER)</td>
                            <td class="metric-value">{metrics['oer']:.2f}%</td>
                            <td>30-50%</td>
                            <td class="{'positive' if metrics['oer'] <= 50 else 'negative' if metrics['oer'] > 60 else 'neutral'}">
                                {'Excellent' if metrics['oer'] <= 35 else 'Good' if metrics['oer'] <= 50 else 'Fair' if metrics['oer'] <= 60 else 'Poor'}
                            </td>
                        </tr>
                        <tr>
                            <td>Return on Investment (ROI)</td>
                            <td class="metric-value">{metrics['roi']:.2f}%</td>
                            <td>10-20%</td>
                            <td class="{'positive' if metrics['roi'] >= 10 else 'negative' if metrics['roi'] < 5 else 'neutral'}">
                                {'Excellent' if metrics['roi'] >= 20 else 'Good' if metrics['roi'] >= 10 else 'Fair' if metrics['roi'] >= 5 else 'Poor'}
                            </td>
                        </tr>
                        <tr>
                            <td>Occupancy Rate</td>
                            <td class="metric-value">{metrics['occupancy_rate']:.2f}%</td>
                            <td>90-95%</td>
                            <td class="{'positive' if metrics['occupancy_rate'] >= 90 else 'negative' if metrics['occupancy_rate'] < 70 else 'neutral'}">
                                {'Excellent' if metrics['occupancy_rate'] >= 95 else 'Good' if metrics['occupancy_rate'] >= 90 else 'Fair' if metrics['occupancy_rate'] >= 70 else 'Poor'}
                            </td>
                        </tr>
                        <tr>
                            <td>Net Yield</td>
                            <td class="metric-value">{metrics['net_yield']:.2f}%</td>
                            <td>5-10%</td>
                            <td class="{'positive' if metrics['net_yield'] >= 5 else 'negative' if metrics['net_yield'] < 3 else 'neutral'}">
                                {'Excellent' if metrics['net_yield'] >= 8 else 'Good' if metrics['net_yield'] >= 5 else 'Fair' if metrics['net_yield'] >= 3 else 'Poor'}
                            </td>
                        </tr>
                        <tr>
                            <td>Break-Even Ratio</td>
                            <td class="metric-value">{metrics['break_even_ratio']:.2f}%</td>
                            <td>< 85%</td>
                            <td class="{'positive' if metrics['break_even_ratio'] < 85 else 'negative' if metrics['break_even_ratio'] > 95 else 'neutral'}">
                                {'Excellent' if metrics['break_even_ratio'] < 75 else 'Good' if metrics['break_even_ratio'] < 85 else 'Fair' if metrics['break_even_ratio'] < 95 else 'Poor'}
                            </td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="analysis-section">
                    <h2>💡 Investment Analysis & Recommendations</h2>
                    <h3>Overall Score: {analysis['score']}/100</h3>
                    
                    <h4>Summary:</h4>
                    <ul>
                        {''.join([f'<li>{s}</li>' for s in analysis['summary']])}
                    </ul>
                    
                    <h4>Recommendations:</h4>
                    <div class="recommendation">
                        <ul>
                            {''.join([f'<li>{r}</li>' for r in analysis['recommendations']])}
                        </ul>
                    </div>
                    
                    {'<h4>Warnings:</h4><div class="warning"><ul>' + ''.join([f'<li>{w}</li>' for w in analysis['warnings']]) + '</ul></div>' if analysis['warnings'] else ''}
                    {'<h4>Risks:</h4><div class="risk"><ul>' + ''.join([f'<li>{r}</li>' for r in analysis['risks']]) + '</ul></div>' if analysis['risks'] else ''}
                </div>

                <div class="footer">
                    <p>This report is for informational purposes only and does not constitute financial advice. Consult with a qualified professional before making investment decisions.</p>
                    <p>&copy; {datetime.now().year} Real Estate Management System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    
    def generate_pdf_report(self, property_data: Dict[str, Any], metrics: Dict[str, float]) -> bytes:
        """Generate comprehensive PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = self.styles
        
        story = []
        
        # Title
        story.append(Paragraph("🏠 Real Estate Investment Analysis", styles["CustomTitle"]))
        story.append(Paragraph("Comprehensive Property Investment Report", styles["h2"]))
        story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))
        
        # Property Overview
        story.append(Paragraph("🏠 Property Overview", styles["CustomHeading"]))
        story.append(Spacer(1, 0.1 * inch))
        
        property_data_table = [
            ["Address:", property_data.get('address', 'N/A')],
            ["Purchase Price:", f"${property_data.get('price', 0):,.2f}"],
            ["Square Footage:", f"{property_data.get('square_footage', 0):,} sq ft"],
            ["Property Type:", property_data.get('property_type', 'N/A')],
            ["Bedrooms:", property_data.get('bedrooms', 0)],
            ["Bathrooms:", property_data.get('bathrooms', 0)],
            ["Year Built:", property_data.get('year_built', 'N/A')],
            ["Lot Size:", f"{property_data.get('lot_size', 0):,.0f} sq ft"]
        ]
        
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ecf0f1'))
        ])
        
        t = Table(property_data_table, colWidths=[2 * inch, 4 * inch])
        t.setStyle(table_style)
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        
        # Financial Summary
        story.append(Paragraph("💰 Financial Summary", styles["CustomHeading"]))
        story.append(Spacer(1, 0.1 * inch))
        
        financial_data_table = [
            ["Net Operating Income:", f"${property_data.get('noi', 0):,.2f}"],
            ["Cash Invested:", f"${property_data.get('cash_invested', 0):,.2f}"],
            ["Gross Rental Income:", f"${property_data.get('gross_rental_income', 0):,.2f}"],
            ["Operating Expenses:", f"${property_data.get('operating_expenses', 0):,.2f}"]
        ]
        
        t = Table(financial_data_table, colWidths=[2 * inch, 4 * inch])
        t.setStyle(table_style)
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        
        # Investment Metrics
        story.append(Paragraph("📊 Investment Metrics", styles["CustomHeading"]))
        story.append(Spacer(1, 0.1 * inch))
        
        metrics_data = [
            ["Metric", "Value", "Industry Benchmark", "Assessment"],
            ["Annual Cash Flow", f"${metrics['annual_cash_flow']:,.2f}", "Positive", 'Excellent' if metrics['annual_cash_flow'] > 0 else 'Needs Improvement'],
            ["Cash-on-Cash Return", f"{metrics['cash_on_cash_return']:.2f}%", "8-12%", 'Excellent' if metrics['cash_on_cash_return'] >= 12 else 'Good' if metrics['cash_on_cash_return'] >= 8 else 'Fair' if metrics['cash_on_cash_return'] >= 5 else 'Poor'],
            ["Cap Rate", f"{metrics['cap_rate']:.2f}%", "6-10%", 'Excellent' if metrics['cap_rate'] >= 8 else 'Good' if metrics['cap_rate'] >= 6 else 'Fair' if metrics['cap_rate'] >= 4 else 'Poor'],
            ["Debt Service Coverage Ratio", f"{metrics['dscr']:.2f}", "1.25+", 'Excellent' if metrics['dscr'] >= 1.5 else 'Good' if metrics['dscr'] >= 1.25 else 'Fair' if metrics['dscr'] >= 1.0 else 'Poor'],
            ["Gross Rental Yield", f"{metrics['gross_rental_yield']:.2f}%", "8-12%", 'Excellent' if metrics['gross_rental_yield'] >= 10 else 'Good' if metrics['gross_rental_yield'] >= 8 else 'Fair' if metrics['gross_rental_yield'] >= 6 else 'Poor'],
            ["Price per Square Foot", f"${metrics['price_per_sqft']:.2f}", "Market Dependent", "Market Analysis Required"],
            ["Operating Expense Ratio (OER)", f"{metrics['oer']:.2f}%", "30-50%", 'Excellent' if metrics['oer'] <= 35 else 'Good' if metrics['oer'] <= 50 else 'Fair' if metrics['oer'] <= 60 else 'Poor'],
            ["Return on Investment (ROI)", f"{metrics['roi']:.2f}%", "10-20%", 'Excellent' if metrics['roi'] >= 20 else 'Good' if metrics['roi'] >= 10 else 'Fair' if metrics['roi'] >= 5 else 'Poor'],
            ["Occupancy Rate", f"{metrics['occupancy_rate']:.2f}%", "90-95%", 'Excellent' if metrics['occupancy_rate'] >= 95 else 'Good' if metrics['occupancy_rate'] >= 90 else 'Fair' if metrics['occupancy_rate'] >= 70 else 'Poor'],
            ["Net Yield", f"{metrics['net_yield']:.2f}%", "5-10%", 'Excellent' if metrics['net_yield'] >= 8 else 'Good' if metrics['net_yield'] >= 5 else 'Fair' if metrics['net_yield'] >= 3 else 'Poor'],
            ["Break-Even Ratio", f"{metrics['break_even_ratio']:.2f}%", "< 85%", 'Excellent' if metrics['break_even_ratio'] < 75 else 'Good' if metrics['break_even_ratio'] < 85 else 'Fair' if metrics['break_even_ratio'] < 95 else 'Poor']
        ]
        
        metrics_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ecf0f1'))
        ])
        
        t = Table(metrics_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        t.setStyle(metrics_table_style)
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        
        # Investment Analysis & Recommendations
        analysis = self._generate_investment_analysis(metrics)
        story.append(Paragraph("💡 Investment Analysis & Recommendations", styles["CustomHeading"]))
        story.append(Spacer(1, 0.1 * inch))
        
        story.append(Paragraph(f"Overall Score: {analysis['score']}/100", styles["h3"]))
        story.append(Spacer(1, 0.1 * inch))
        
        story.append(Paragraph("Summary:", styles["h4"]))
        for s in analysis['summary']:
            story.append(Paragraph(f"• {s}", styles["CustomBody"]))
        story.append(Spacer(1, 0.1 * inch))
        
        story.append(Paragraph("Recommendations:", styles["h4"]))
        for r in analysis['recommendations']:
            story.append(Paragraph(f"• {r}", styles["CustomBody"]))
        story.append(Spacer(1, 0.1 * inch))
        
        if analysis['warnings']:
            story.append(Paragraph("Warnings:", styles["h4"]))
            for w in analysis['warnings']:
                story.append(Paragraph(f"• {w}", styles["CustomBody"]))
            story.append(Spacer(1, 0.1 * inch))
            
        if analysis['risks']:
            story.append(Paragraph("Risks:", styles["h4"]))
            for r in analysis['risks']:
                story.append(Paragraph(f"• {r}", styles["CustomBody"]))
            story.append(Spacer(1, 0.1 * inch))
            
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_csv_report(self, property_data: Dict[str, Any], metrics: Dict[str, float]) -> str:
        """Generate CSV report"""
        df_property = pd.DataFrame([property_data])
        df_metrics = pd.DataFrame([metrics])
        
        # Combine dataframes
        combined_df = pd.concat([df_property, df_metrics], axis=1)
        
        return combined_df.to_csv(index=False)
    
    def generate_json_report(self, property_data: Dict[str, Any], metrics: Dict[str, float]) -> str:
        """Generate JSON report"""
        report_data = {
            "property_data": property_data,
            "investment_metrics": metrics,
            "analysis": self._generate_investment_analysis(metrics),
            "report_generated_at": datetime.now().isoformat()
        }
        return json.dumps(report_data, indent=4)

def create_report_generator() -> ReportGenerator:
    """Create and return a report generator instance"""
    return ReportGenerator()


def get_demo_data():
    """Returns a sample DataFrame for demonstration purposes."""
    sample_data = {
        'id': ['1', '2', '3', '4', '5'],
        'city': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento', 'Oakland'],
        'state': ['CA', 'CA', 'CA', 'CA', 'CA'],
        'zipCode': ['90210', '94102', '92101', '95814', '94612'],
        'propertyType': ['Single Family', 'Condo', 'Townhouse', 'Single Family', 'Condo'],
        'bedrooms': [3, 2, 4, 3, 1],
        'bathrooms': [2.5, 2.0, 3.0, 2.0, 1.0],
        'squareFootage': [1800, 1200, 2200, 1600, 800],
        'yearBuilt': [1995, 2005, 1988, 2000, 2015],
        'formattedAddress': [
            '123 Beverly Hills Dr, Los Angeles, CA 90210',
            '456 Market St, San Francisco, CA 94102',
            '789 Harbor View, San Diego, CA 92101',
            '101 Capitol Mall, Sacramento, CA 95814',
            '200 Grand Ave, Oakland, CA 94612'
        ],
        'price': [850000, 1200000, 750000, 600000, 450000],
        'propertyTaxes': [10000, 15000, 8000, 7000, 5000],
        'hoa': [0, 300, 150, 0, 250],
        'lotSize': [7000, 0, 3000, 6500, 0]
    }
    return pd.DataFrame(sample_data)

def main():
    st.title("🏠 Real Estate Management System")
    
    # Sidebar for Google Sheets authentication
    with st.sidebar:
        st.header("🔐 Google Sheets Authentication")
        uploaded_file = st.file_uploader(
            "Upload Google Service Account JSON",
            type=['json'],
            help="Upload your Google Service Account credentials JSON file"
        )
        
        if uploaded_file is not None:
            st.success("✅ Credentials uploaded successfully!")
            # Store credentials in session state
            st.session_state['credentials'] = json.load(uploaded_file)
        
        st.markdown("---")
        st.markdown("### 📊 Sheet Information")
        st.markdown(f"**Sheet URL:** [View Sheet]({GOOGLE_SHEET_URL})")
        st.markdown(f"**Webhook URL:** {N8N_WEBHOOK_URL}")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Property Listings", "📍 Address Submission", "📊 Property Input", "📈 Reports"])
    
    with tab1:
        property_listings_tab()
    
    with tab2:
        address_submission_tab()
    
    with tab3:
        property_input_tab()
    
    with tab4:
        reports_tab()

def load_google_sheets_data() -> Optional[pd.DataFrame]:
    """Load data from Google Sheets using the session-managed sheets_manager"""
    sheets_manager = get_sheet_manager()
    if sheets_manager:
        if sheets_manager.connect_to_sheet("1BWz_FnYdzZyyl4WafSgoZV9rLHC91XOjstDcgwn_k6Y"): # Hardcoded Sheet ID
            return sheets_manager.get_all_data()
    return None

def apply_filters(df: pd.DataFrame, search_term: str, property_type_filter: str) -> pd.DataFrame:
    """Apply search and filter to the dataframe"""
    sheets_manager = get_sheet_manager()
    if sheets_manager is None:
        return df # Should not happen if sheets_manager is properly initialized

    df = sheets_manager.search_data(df, search_term, columns=['formattedAddress', 'city', 'state', 'propertyType'])
    df = sheets_manager.filter_by_property_type(df, property_type_filter)
    
    return df

def display_property_cards(df):
    """Display properties in card format"""
    if df.empty:
        st.info("No properties found matching your criteria.")
        return
    
    # Display properties in rows of 2
    for i in range(0, len(df), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            if i < len(df):
                display_single_property_card(df.iloc[i], i)
        
        with col2:
            if i + 1 < len(df):
                display_single_property_card(df.iloc[i + 1], i + 1)

def display_single_property_card(property_data, index):
    """Display a single property card with selection option"""
    # Handle missing or empty values
    address = property_data.get('formattedAddress', property_data.get('addressLine1', 'Address not available'))
    city = property_data.get('city', 'N/A')
    state = property_data.get('state', 'N/A')
    property_type = property_data.get('propertyType', 'N/A')
    bedrooms = property_data.get('bedrooms', 'N/A')
    bathrooms = property_data.get('bathrooms', 'N/A')
    square_footage = property_data.get('squareFootage', 'N/A')
    year_built = property_data.get('yearBuilt', 'N/A')
    price = property_data.get('price', 'N/A')
    
    # Check if this property is currently selected
    is_selected = False
    if 'property_selected' in st.session_state and st.session_state['property_selected']:
        selected_property = st.session_state.get('selected_property', {})
        selected_address = selected_property.get('formattedAddress', selected_property.get('addressLine1', ''))
        current_address = property_data.get('formattedAddress', property_data.get('addressLine1', ''))
        is_selected = selected_address == current_address
    
    # Create a unique key for this property
    property_key = f"property_{index}_{hash(str(property_data))}"
    
    # Apply selected styling if this property is selected
    card_class = "property-card selected-property" if is_selected else "property-card"
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        card_content = f"""
        <div class="{card_class}">
            {f'<div class="selection-indicator">✓ SELECTED</div>' if is_selected else ''}
            <h4>🏠 {address}</h4>
            <p><strong>📍 Location:</strong> {city}, {state}</p>
            <p><strong>🏘️ Type:</strong> {property_type}</p>
            <p><strong>🛏️ Bedrooms:</strong> {bedrooms} | <strong>🚿 Bathrooms:</strong> {bathrooms}</p>
            <p><strong>📐 Square Footage:</strong> {square_footage} | <strong>📅 Year Built:</strong> {year_built}</p>
            {f'<p><strong>💰 Price:</strong> ${float(price):,.2f}</p>' if price != 'N/A' and str(price).replace('.','').replace(',','').isdigit() else ''}
        </div>
        """
        st.markdown(card_content, unsafe_allow_html=True)
    
    with col2:
        if is_selected:
            st.markdown("### ✅")
            st.markdown("**Selected**")
            if st.button("🔄 Reselect", key=f"reselect_{property_key}", use_container_width=True):
                # Re-store selected property data in session state
                st.session_state['selected_property'] = property_data
                st.session_state['property_selected'] = True
                st.success("✅ Property reselected!")
                st.rerun()
        else:
            if st.button("📊 Select for Analysis", key=property_key, use_container_width=True):
                # Store selected property data in session state
                st.session_state['selected_property'] = property_data
                st.session_state['property_selected'] = True
                st.success("✅ Property selected! Go to Property Input tab to review and complete the data.")
                st.rerun()

def property_listings_tab():
    st.header("📋 Property Listings")
    
    # Show selection status
    if 'property_selected' in st.session_state and st.session_state['property_selected']:
        selected_property = st.session_state.get('selected_property', {})
        st.info(f"🎯 **Currently Selected:** {selected_property.get('formattedAddress', selected_property.get('addressLine1', 'Unknown Address'))}")
    
    # Search functionality
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search properties", placeholder="Enter city, state, or property type...")
    with col2:
        property_type_filter = st.selectbox("Property Type", ["All", "Single Family", "Condo", "Townhouse", "Multi-Family"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Price", "City", "Square Footage", "Year Built"])
    
    # Data source selection
    data_source = st.radio("Select Data Source", ('Live Google Sheet', 'Demo Data'), horizontal=True)

    if data_source == 'Live Google Sheet':
        if 'credentials' in st.session_state:
            try:
                df = load_google_sheets_data()
                if df is not None and not df.empty:
                    # Apply filters
                    filtered_df = apply_filters(df, search_term, property_type_filter)
                    
                    # Show count
                    st.markdown(f"**Found {len(filtered_df)} properties**")
                    
                    # Display properties in cards
                    display_property_cards(filtered_df)
                else:
                    st.info("No data found in the Google Sheet.")
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")
        else:
            st.warning("Please upload Google Service Account credentials in the sidebar to view live property listings.")
    else: # Demo Data
        df = get_demo_data()
        filtered_df = apply_filters(df, search_term, property_type_filter)
        st.markdown(f"**Found {len(filtered_df)} properties**")
        display_property_cards(filtered_df)
        
        # Show sample data structure
        st.markdown("### 📊 Expected Google Sheets Data Structure")
        st.markdown("""
        Your Google Sheet should contain the following columns:
        - **id**: Unique identifier
        - **city**: Property city
        - **state**: Property state  
        - **zipCode**: ZIP code
        - **latitude**: Latitude coordinate
        - **longitude**: Longitude coordinate
        - **propertyType**: Type of property (Single Family, Condo, etc.)
        - **bedrooms**: Number of bedrooms
        - **bathrooms**: Number of bathrooms
        - **squareFootage**: Square footage
        - **lotSize**: Lot size in square feet
        - **yearBuilt**: Year the property was built
        - **formattedAddress**: Full formatted address
        - **addressLine1**: Primary address line
        - **price**: Property price (optional)
        - **propertyTaxes**: Annual property taxes (optional)
        - **hoa**: HOA fees (optional)
        """)
        
        # Add sample data
        sample_data = {
            'id': ['1', '2', '3'],
            'city': ['Los Angeles', 'San Francisco', 'San Diego'],
            'state': ['CA', 'CA', 'CA'],
            'zipCode': ['90210', '94102', '92101'],
            'propertyType': ['Single Family', 'Condo', 'Townhouse'],
            'bedrooms': [3, 2, 4],
            'bathrooms': [2.5, 2.0, 3.0],
            'squareFootage': [1800, 1200, 2200],
            'yearBuilt': [1995, 2005, 1988],
            'formattedAddress': ['123 Beverly Hills Dr, Los Angeles, CA 90210', '456 Market St, San Francisco, CA 94102', '789 Harbor View, San Diego, CA 92101'],
            'price': [850000, 1200000, 750000]
        }
        
        import pandas as pd
        sample_df = pd.DataFrame(sample_data)
        st.markdown("### 📋 Sample Data")
        st.dataframe(sample_df, use_container_width=True)

def address_submission_tab():
    st.header("📍 Address Submission to n8n")
    
    st.markdown("Submit property addresses to the n8n webhook for processing.")
    
    # Test webhook connection
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔗 Test Connection"):
            webhook_manager = create_webhook_manager(N8N_WEBHOOK_URL)
            test_result = webhook_manager.test_webhook_connection()
            
            if test_result['success']:
                st.success(f"✅ Connection successful! Response time: {test_result['response_time']:.2f}s")
            else:
                st.error(f"❌ Connection failed: {test_result.get('error', 'Unknown error')}")
    
    with st.form("address_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            address_line1 = st.text_input("Address Line 1*", placeholder="123 Main Street")
            city = st.text_input("City*", placeholder="Anytown")
            state = st.text_input("State*", placeholder="CA")
            zip_code = st.text_input("ZIP Code*", placeholder="12345")
        
        with col2:
            address_line2 = st.text_input("Address Line 2", placeholder="Apt 4B (optional)")
            county = st.text_input("County", placeholder="County Name")
            property_type = st.selectbox("Property Type", ["Single Family", "Condo", "Townhouse", "Multi-Family", "Commercial"])
            notes = st.text_area("Additional Notes", placeholder="Any additional information...")
        
        submitted = st.form_submit_button("📤 Submit Address", use_container_width=True)
        
        if submitted:
            if address_line1 and city and state and zip_code:
                # Create webhook manager
                webhook_manager = create_webhook_manager(N8N_WEBHOOK_URL)
                
                # Prepare form data
                form_data = {
                    "addressLine1": address_line1,
                    "addressLine2": address_line2,
                    "city": city,
                    "state": state,
                    "zipCode": zip_code,
                    "county": county,
                    "propertyType": property_type,
                    "notes": notes
                }
                
                # Validate and format data
                validation_result = webhook_manager.validate_address_data(form_data)
                
                if validation_result['valid']:
                    # Format the data
                    formatted_data = webhook_manager.format_address_data(form_data)
                    
                    # Send to webhook
                    result = webhook_manager.send_address_data(formatted_data)
                    
                    # Display result
                    display_webhook_result(result)
                    
                    # Show warnings if any
                    if validation_result['warnings']:
                        with st.expander("⚠️ Validation Warnings"):
                            for warning in validation_result['warnings']:
                                st.warning(warning)
                else:
                    st.error("❌ Please fix the following errors:")
                    for error in validation_result['errors']:
                        st.error(f"• {error}")
            else:
                st.error("Please fill in all required fields (marked with *).")

def property_input_tab():
    st.header("📊 Property Input for Reports")
    
    # Check if a property was selected from listings
    if 'property_selected' in st.session_state and st.session_state['property_selected']:
        selected_property = st.session_state.get('selected_property', {})
        st.success(f"✅ Property selected: {selected_property.get('formattedAddress', selected_property.get('addressLine1', 'Unknown Address'))}")
        
        # Option to clear selection
        if st.button("🔄 Clear Selection and Start Fresh"):
            st.session_state['property_selected'] = False
            st.session_state['selected_property'] = {}
            st.rerun()
    
    st.markdown("Enter property details to generate investment analysis reports.")
    
    # Get default values from selected property or use defaults
    selected_property = st.session_state.get('selected_property', {}) if st.session_state.get('property_selected', False) else {}
    
    with st.form("property_input_form"):
        # Property Details
        st.subheader("🏠 Property Details")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            address = st.text_input(
                "Property Address*", 
                value=selected_property.get('formattedAddress', selected_property.get('addressLine1', '')),
                placeholder="1234 Example St, Anytown, USA"
            )
            price = st.number_input(
                "Property Price ($)*", 
                min_value=0.0, 
                value=float(selected_property.get('price', 350000.00)) if selected_property.get('price') and str(selected_property.get('price')).replace('.','').replace(',','').isdigit() else 350000.00,
                format="%.2f"
            )
            square_footage = st.number_input(
                "Square Footage*", 
                min_value=0, 
                value=int(selected_property.get('squareFootage', 1500)) if selected_property.get('squareFootage') and str(selected_property.get('squareFootage')).isdigit() else 1500
            )
        
        with col2:
            bedrooms = st.number_input(
                "Bedrooms", 
                min_value=0, 
                value=int(selected_property.get('bedrooms', 3)) if selected_property.get('bedrooms') and str(selected_property.get('bedrooms')).isdigit() else 3
            )
            bathrooms = st.number_input(
                "Bathrooms", 
                min_value=0.0, 
                step=0.5, 
                value=float(selected_property.get('bathrooms', 2.0)) if selected_property.get('bathrooms') and str(selected_property.get('bathrooms')).replace('.','').replace(',','').isdigit() else 2.0
            )
            year_built = st.number_input(
                "Year Built", 
                min_value=1800, 
                max_value=2100, 
                value=int(selected_property.get('yearBuilt', 1990)) if selected_property.get('yearBuilt') and str(selected_property.get('yearBuilt')).isdigit() else 1990
            )
        
        with col3:
            property_type = st.selectbox(
                "Property Type", 
                ["Single Family", "Condo", "Townhouse", "Multi-Family", "Commercial"],
                index=["Single Family", "Condo", "Townhouse", "Multi-Family", "Commercial"].index(selected_property.get('propertyType', 'Single Family')) if selected_property.get('propertyType') in ["Single Family", "Condo", "Townhouse", "Multi-Family", "Commercial"] else 0
            )
            lot_size = st.number_input(
                "Lot Size (sq ft)", 
                min_value=0.0, 
                value=float(selected_property.get('lotSize', 6000.0)) if selected_property.get('lotSize') and str(selected_property.get('lotSize')).replace('.','').replace(',','').isdigit() else 6000.0
            )
            zoning = st.text_input(
                "Zoning", 
                value=selected_property.get('zoning', ''),
                placeholder="R-1"
            )
        
        # Financial Details
        st.subheader("💰 Financial Details")
        st.info("💡 The following financial data is typically not available in property listings and needs to be researched or estimated.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            noi = st.number_input("Net Operating Income (NOI) ($)*", min_value=0.0, value=20000.00, format="%.2f")
            cash_invested = st.number_input("Cash Invested ($)*", min_value=0.0, value=70000.00, format="%.2f")
            gross_rental_income = st.number_input("Gross Rental Income ($)*", min_value=0.0, value=36000.00, format="%.2f")
        
        with col2:
            operating_expenses = st.number_input("Operating Expenses ($)*", min_value=0.0, value=10000.00, format="%.2f")
            total_debt_service = st.number_input("Total Debt Service ($)*", min_value=0.0, value=15000.00, format="%.2f")
            property_taxes = st.number_input(
                "Property Taxes ($)", 
                min_value=0.0, 
                value=float(selected_property.get('propertyTaxes', 3500.0)) if selected_property.get('propertyTaxes') and str(selected_property.get('propertyTaxes')).replace('.','').replace(',','').isdigit() else 3500.0,
                format="%.2f"
            )
        
        with col3:
            occupied_units = st.number_input("Occupied Units", min_value=0, value=1)
            total_units = st.number_input("Total Units", min_value=1, value=1)
            hoa_fees = st.number_input(
                "HOA Fees ($)", 
                min_value=0.0, 
                value=float(selected_property.get('hoa', 0.0)) if selected_property.get('hoa') and str(selected_property.get('hoa')).replace('.','').replace(',','').isdigit() else 0.0,
                format="%.2f"
            )
        
        submitted = st.form_submit_button("💾 Save Property Data", use_container_width=True)
        
        if submitted:
            if address and price > 0 and square_footage > 0 and noi >= 0 and cash_invested >= 0:
                # Calculate annual cash flow
                annual_cash_flow = gross_rental_income - operating_expenses
                
                # Store property data in session state
                st.session_state['property_data'] = {
                    "address": address,
                    "price": price,
                    "square_footage": square_footage,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "year_built": year_built,
                    "property_type": property_type,
                    "lot_size": lot_size,
                    "zoning": zoning,
                    "noi": noi,
                    "cash_invested": cash_invested,
                    "gross_rental_income": gross_rental_income,
                    "operating_expenses": operating_expenses,
                    "total_debt_service": total_debt_service,
                    "property_taxes": property_taxes,
                    "occupied_units": occupied_units,
                    "total_units": total_units,
                    "hoa_fees": hoa_fees,
                    "annual_cash_flow": annual_cash_flow,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Clear the property selection after saving
                if 'property_selected' in st.session_state:
                    st.session_state['property_selected'] = False
                    st.session_state['selected_property'] = {}
                
                st.success("✅ Property data saved successfully! You can now generate reports in the Reports tab.")
            else:
                st.error("Please fill in all required fields (marked with *).")

def reports_tab():
    st.header("📈 Investment Reports")
    
    report_generator = create_report_generator()
    
    if 'property_data' in st.session_state:
        property_data = st.session_state['property_data']
        metrics = report_generator.calculate_investment_metrics(property_data)
        analysis = report_generator._generate_investment_analysis(metrics)
        
        st.subheader("Property Details")
        st.json(property_data)
        
        st.subheader("Investment Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Cap Rate", value=f"{metrics['cap_rate']:.2f}%")
            st.metric(label="Cash-on-Cash Return", value=f"{metrics['cash_on_cash_return']:.2f}%")
            st.metric(label="Debt Service Coverage Ratio", value=f"{metrics['dscr']:.2f}")
        with col2:
            st.metric(label="Gross Rental Yield", value=f"{metrics['gross_rental_yield']:.2f}%")
            st.metric(label="Operating Expense Ratio", value=f"{metrics['oer']:.2f}%")
            st.metric(label="Return on Investment (ROI)", value=f"{metrics['roi']:.2f}%")
        with col3:
            st.metric(label="Occupancy Rate", value=f"{metrics['occupancy_rate']:.2f}%")
            st.metric(label="Net Yield", value=f"{metrics['net_yield']:.2f}%")
            st.metric(label="Break-Even Ratio", value=f"{metrics['break_even_ratio']:.2f}%")
        
        st.subheader("Investment Analysis")
        st.write(f"**Overall Score:** {analysis['score']}/100")
        
        st.markdown("**Summary:**")
        for s in analysis['summary']:
            st.success(f"• {s}")
            
        if analysis['recommendations']:
            st.markdown("**Recommendations:**")
            for r in analysis['recommendations']:
                st.info(f"• {r}")
                
        if analysis['warnings']:
            st.markdown("**Warnings:**")
            for w in analysis['warnings']:
                st.warning(f"• {w}")
                
        if analysis['risks']:
            st.markdown("**Risks:**")
            for r in analysis['risks']:
                st.error(f"• {r}")
        
        st.subheader("Download Reports")
        col1, col2, col3 = st.columns(3)
        
        # HTML Report
        html_report = report_generator.generate_html_report(property_data, metrics)
        with col1:
            st.download_button(
                label="Download HTML Report",
                data=html_report,
                file_name="investment_report.html",
                mime="text/html",
                use_container_width=True
            )
            
        # PDF Report
        pdf_report = report_generator.generate_pdf_report(property_data, metrics)
        with col2:
            st.download_button(
                label="Download PDF Report",
                data=pdf_report,
                file_name="investment_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        # CSV Report
        csv_report = report_generator.generate_csv_report(property_data, metrics)
        with col3:
            st.download_button(
                label="Download CSV Report",
                data=csv_report,
                file_name="investment_report.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        # JSON Report
        json_report = report_generator.generate_json_report(property_data, metrics)
        st.download_button(
            label="Download JSON Report",
            data=json_report,
            file_name="investment_report.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Save to Google Sheets
        st.subheader("Save Analysis to Google Sheets")
        if st.button("💾 Save Analysis to Google Sheets", use_container_width=True):
            sheets_manager = get_sheet_manager()
            if sheets_manager:
                try:
                    # Prepare data for Google Sheets
                    # Ensure the order matches your Google Sheet columns
                    # id, city, state, zipCode, latitude, longitude, propertyType, bedrooms, bathrooms, squareFootage, lotSize, yearBuilt, assessorID, legalDescription, subdivision, zoning, lastSaleDate, hoa, features, taxAssessments, propertyTaxes, history, owner, ownerOccupied, formattedAddress, addressLine1, addressLine2, county, price, noi, cash_invested, gross_rental_income, operating_expenses, total_debt_service, annual_cash_flow, cap_rate, cash_on_cash_return, dscr, gross_rental_yield, price_per_sqft, oer, roi, occupancy_rate, net_yield, break_even_ratio, score, summary, recommendations, warnings, risks, timestamp
                    
                    # Create a dictionary with all relevant data
                    all_data = {
                        "id": property_data.get("id", ""),
                        "city": property_data.get("city", ""),
                        "state": property_data.get("state", ""),
                        "zipCode": property_data.get("zipCode", ""),
                        "latitude": property_data.get("latitude", ""),
                        "longitude": property_data.get("longitude", ""),
                        "propertyType": property_data.get("property_type", ""),
                        "bedrooms": property_data.get("bedrooms", ""),
                        "bathrooms": property_data.get("bathrooms", ""),
                        "squareFootage": property_data.get("square_footage", ""),
                        "lotSize": property_data.get("lot_size", ""),
                        "yearBuilt": property_data.get("year_built", ""),
                        "assessorID": property_data.get("assessorID", ""),
                        "legalDescription": property_data.get("legalDescription", ""),
                        "subdivision": property_data.get("subdivision", ""),
                        "zoning": property_data.get("zoning", ""),
                        "lastSaleDate": property_data.get("lastSaleDate", ""),
                        "hoa": property_data.get("hoa_fees", ""),
                        "features": property_data.get("features", ""),
                        "taxAssessments": property_data.get("taxAssessments", ""),
                        "propertyTaxes": property_data.get("property_taxes", ""),
                        "history": property_data.get("history", ""),
                        "owner": property_data.get("owner", ""),
                        "ownerOccupied": property_data.get("ownerOccupied", ""),
                        "formattedAddress": property_data.get("address", ""),
                        "addressLine1": property_data.get("addressLine1", ""),
                        "addressLine2": property_data.get("addressLine2", ""),
                        "county": property_data.get("county", ""),
                        "price": property_data.get("price", ""),
                        "noi": property_data.get("noi", ""),
                        "cash_invested": property_data.get("cash_invested", ""),
                        "gross_rental_income": property_data.get("gross_rental_income", ""),
                        "operating_expenses": property_data.get("operating_expenses", ""),
                        "total_debt_service": property_data.get("total_debt_service", ""),
                        "annual_cash_flow": property_data.get("annual_cash_flow", ""),
                        "cap_rate": metrics.get("cap_rate", ""),
                        "cash_on_cash_return": metrics.get("cash_on_cash_return", ""),
                        "dscr": metrics.get("dscr", ""),
                        "gross_rental_yield": metrics.get("gross_rental_yield", ""),
                        "price_per_sqft": metrics.get("price_per_sqft", ""),
                        "oer": metrics.get("oer", ""),
                        "roi": metrics.get("roi", ""),
                        "occupancy_rate": metrics.get("occupancy_rate", ""),
                        "net_yield": metrics.get("net_yield", ""),
                        "break_even_ratio": metrics.get("break_even_ratio", ""),
                        "score": analysis.get("score", ""),
                        "summary": "; ".join(analysis.get("summary", [])),
                        "recommendations": "; ".join(analysis.get("recommendations", [])),
                        "warnings": "; ".join(analysis.get("warnings", [])),
                        "risks": "; ".join(analysis.get("risks", [])),
                        "timestamp": property_data.get("timestamp", "")
                    }
                    
                    # Convert to a list of values in the correct order for appending
                    # This order must match your Google Sheet's column order exactly
                    row_to_append = [
                        all_data.get("id", ""),
                        all_data.get("city", ""),
                        all_data.get("state", ""),
                        all_data.get("zipCode", ""),
                        all_data.get("latitude", ""),
                        all_data.get("longitude", ""),
                        all_data.get("propertyType", ""),
                        all_data.get("bedrooms", ""),
                        all_data.get("bathrooms", ""),
                        all_data.get("squareFootage", ""),
                        all_data.get("lotSize", ""),
                        all_data.get("yearBuilt", ""),
                        all_data.get("assessorID", ""),
                        all_data.get("legalDescription", ""),
                        all_data.get("subdivision", ""),
                        all_data.get("zoning", ""),
                        all_data.get("lastSaleDate", ""),
                        all_data.get("hoa", ""),
                        all_data.get("features", ""),
                        all_data.get("taxAssessments", ""),
                        all_data.get("propertyTaxes", ""),
                        all_data.get("history", ""),
                        all_data.get("owner", ""),
                        all_data.get("ownerOccupied", ""),
                        all_data.get("formattedAddress", ""),
                        all_data.get("addressLine1", ""),
                        all_data.get("addressLine2", ""),
                        all_data.get("county", ""),
                        all_data.get("price", ""),
                        all_data.get("noi", ""),
                        all_data.get("cash_invested", ""),
                        all_data.get("gross_rental_income", ""),
                        all_data.get("operating_expenses", ""),
                        all_data.get("total_debt_service", ""),
                        all_data.get("annual_cash_flow", ""),
                        all_data.get("cap_rate", ""),
                        all_data.get("cash_on_cash_return", ""),
                        all_data.get("dscr", ""),
                        all_data.get("gross_rental_yield", ""),
                        all_data.get("price_per_sqft", ""),
                        all_data.get("oer", ""),
                        all_data.get("roi", ""),
                        all_data.get("occupancy_rate", ""),
                        all_data.get("net_yield", ""),
                        all_data.get("break_even_ratio", ""),
                        all_data.get("score", ""),
                        all_data.get("summary", ""),
                        all_data.get("recommendations", ""),
                        all_data.get("warnings", ""),
                        all_data.get("risks", ""),
                        all_data.get("timestamp", "")
                    ]
                    
                    if sheets_manager.connect_to_sheet("1BWz_FnYdzZyyl4WafSgoZV9rLHC91XOjstDcgwn_k6Y", worksheet_name="Reports"):
                        sheets_manager.append_row(row_to_append)
                        st.success("✅ Analysis saved to Google Sheets successfully!")
                    else:
                        st.error("Failed to connect to the 'Reports' worksheet. Please ensure it exists.")
                except Exception as e:
                    st.error(f"Error saving to Google Sheets: {str(e)}")
            else:
                st.warning("Please upload Google Service Account credentials in the sidebar to save analysis.")
    else:
        st.info("Please enter property data in the 'Property Input' tab first to generate reports.")

if __name__ == "__main__":
    main()


