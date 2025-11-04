"""
Data Parser - Parse AI responses to extract structured data (not configs)

Handles XML responses with extracted data from web pages.
Similar to XMLConfigParser but for data extraction, not config creation.
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import json


class DataParser:
    """
    Parse AI responses that contain extracted data (not scraper configs).
    
    AI returns XML with <extracted_data> containing structured JSON.
    This parser extracts and validates the data.
    """
    
    @staticmethod
    def parse_extracted_data(ai_response: str) -> Dict[str, Any]:
        """
        Parse AI response to extract structured data.
        
        Expected XML format:
        ```xml
        <xml>
          <message>Optional explanation</message>
          <extracted_data>
            <data>
              {"field1": "value1", "field2": 123}
            </data>
          </extracted_data>
          <status>done</status>
        </xml>
        ```
        
        Args:
            ai_response: Raw AI response string
            
        Returns:
            Dictionary with:
            {
                "valid": bool,
                "error": Optional[str],
                "message": Optional[str],
                "data": Optional[Dict/List],  # Extracted structured data
                "done": bool
            }
        """
        result = {
            "valid": False,
            "error": None,
            "message": None,
            "data": None,
            "done": False
        }
        
        try:
            # Clean XML
            cleaned_xml = DataParser._clean_xml(ai_response)
            if not cleaned_xml:
                result["error"] = "No valid XML found in response"
                return result
            
            # Parse XML
            try:
                root = ET.fromstring(cleaned_xml)
            except ET.ParseError as e:
                result["error"] = f"XML parsing error: {str(e)}"
                return result
            
            # Extract components
            if root.tag == "xml":
                # Parse wrapped XML
                result = DataParser._parse_wrapped_data_xml(root, result)
            else:
                result["error"] = f"Expected <xml> root tag, got {root.tag}"
                return result
            
            # Validate
            if not result["data"] and not result["message"]:
                result["error"] = "No extracted data or message found in XML"
                result["valid"] = False
                return result
            
            result["valid"] = True
            return result
            
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            return result
    
    @staticmethod
    def _clean_xml(response: str) -> Optional[str]:
        """
        Clean XML from AI response (remove markdown, extra text, etc.).
        
        Args:
            response: Raw AI response
            
        Returns:
            Cleaned XML string or None if no XML found
        """
        response = response.strip()
        
        # Remove markdown code blocks
        if "```xml" in response:
            start = response.find("```xml")
            end = response.find("```", start + 6)
            if end != -1:
                response = response[start + 6:end].strip()
        elif "```" in response:
            start = response.find("```")
            end = response.find("```", start + 3)
            if end != -1:
                response = response[start + 3:end].strip()
        
        # Find XML boundaries
        start = response.find("<xml>")
        end = response.rfind("</xml>")
        
        if start == -1 or end == -1:
            return None
        
        return response[start:end + 7].strip()
    
    @staticmethod
    def _parse_wrapped_data_xml(root: ET.Element, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse wrapped XML with extracted data.
        
        Args:
            root: XML root element (<xml>)
            result: Result dictionary to populate
            
        Returns:
            Updated result dictionary
        """
        # Extract message
        message_elem = root.find("message")
        if message_elem is not None and message_elem.text:
            result["message"] = message_elem.text.strip()
        
        # Extract status
        status_elem = root.find("status")
        if status_elem is not None and status_elem.text:
            status = status_elem.text.strip().lower()
            result["done"] = (status == "done")
        
        # Extract data
        extracted_data_elem = root.find("extracted_data")
        if extracted_data_elem is not None:
            data_elem = extracted_data_elem.find("data")
            if data_elem is not None:
                data_text = data_elem.text
                if data_text:
                    try:
                        # Parse JSON data
                        result["data"] = json.loads(data_text.strip())
                    except json.JSONDecodeError:
                        # If not JSON, try to parse as structured text
                        result["data"] = DataParser._parse_structured_text(data_text)
        
        return result
    
    @staticmethod
    def _parse_structured_text(text: str) -> Dict[str, Any]:
        """
        Parse structured text data (fallback if not JSON).
        
        Args:
            text: Text content
            
        Returns:
            Dictionary with parsed data
        """
        # Try to extract key-value pairs
        data = {}
        lines = text.strip().split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Try to parse value
                if value.lower() in ("true", "false"):
                    data[key] = value.lower() == "true"
                elif value.isdigit():
                    data[key] = int(value)
                elif value.replace(".", "", 1).isdigit():
                    data[key] = float(value)
                else:
                    data[key] = value
        return data if data else {"raw_text": text}
    
    @staticmethod
    def create_error_feedback(error_message: str) -> str:
        """
        Create error feedback XML for AI.
        
        Args:
            error_message: Error message to send to AI
            
        Returns:
            XML string with error feedback
        """
        return f"""<xml>
  <message>{error_message}</message>
  <status>processing</status>
</xml>"""

