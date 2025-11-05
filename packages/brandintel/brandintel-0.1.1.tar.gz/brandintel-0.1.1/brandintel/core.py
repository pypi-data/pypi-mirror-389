"""
BrandIntel - Brand competitor analysis using Google Gemini AI
"""
import os
import sys
import google.generativeai as genai

# Configure Gemini API
# Users need to set GEMINI_API_KEY environment variable
def _get_gemini_client():
    """Initialize and return Gemini client"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable not set. "
            "Please set it using: export GEMINI_API_KEY='your-api-key'"
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

def get_brand_summary(brand_name):
    """
    Get a summary of a brand using Google Gemini AI.
    
    Args:
        brand_name (str): Name of the brand to analyze
        
    Returns:
        str: Brand summary
    """
    try:
        model = _get_gemini_client()
        prompt = f"Provide a brief summary of the brand '{brand_name}'. Include key information about the brand, its products, market position, and notable characteristics. Keep it concise (2-3 paragraphs)."
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating brand summary: {str(e)}"

def get_competitors_for_brand(brand_name):
    """
    Identify competitor brands for a given brand using Google Gemini AI.
    
    Args:
        brand_name (str): Name of the brand to find competitors for
        
    Returns:
        str: List of competitor brands with brief descriptions
    """
    try:
        model = _get_gemini_client()
        prompt = f"List the main competitors of the brand '{brand_name}'. Provide a list of competitor brand names with brief descriptions of why they compete. Format as a clear list."
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error finding competitors: {str(e)}"

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BrandIntel - Brand competitor analysis')
    parser.add_argument('--brand', type=str, required=True, help='Brand name to analyze')
    parser.add_argument('--summary', action='store_true', help='Get brand summary')
    parser.add_argument('--competitors', action='store_true', help='Get competitors')
    
    args = parser.parse_args()
    
    if args.summary or (not args.summary and not args.competitors):
        print("Brand Summary:")
        print("=" * 60)
        print(get_brand_summary(args.brand))
        print()
    
    if args.competitors or (not args.summary and not args.competitors):
        print("Competitors:")
        print("=" * 60)
        print(get_competitors_for_brand(args.brand))

if __name__ == "__main__":
    main()