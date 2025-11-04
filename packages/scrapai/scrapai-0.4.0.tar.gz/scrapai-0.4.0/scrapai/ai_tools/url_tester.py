"""

URL Tester - Test URLs before creating configurations

"""



import time

from typing import Dict, Optional, List

import requests

from bs4 import BeautifulSoup





class URLTester:

    """Test and analyze URLs before scraping"""



    def __init__(self, proxies: Optional[Dict] = None):

        """

        Initialize URL tester.



        Args:

            proxies: Optional proxy configuration

        """

        self.proxies = proxies



    def test_url_accessibility(self, url: str) -> Dict:

        """

        Test if URL is accessible.



        Args:

            url: URL to test



        Returns:

            Accessibility test result

        """

        result = {

            "url": url,

            "is_accessible": False,

            "status_code": None,

            "content_type": None,

            "response_time_ms": None,

            "error": None,

            "recommendations": []

        }



        try:

            start = time.time()



            response = requests.get(

                url,

                timeout=10,

                headers={"User-Agent": "Mozilla/5.0"},

                proxies=self.proxies

            )



            end = time.time()



            result["is_accessible"] = True

            result["status_code"] = response.status_code

            result["content_type"] = response.headers.get("content-type", "")

            result["response_time_ms"] = int((end - start) * 1000)



            if response.status_code != 200:

                result["recommendations"].append(

                    f"Status {response.status_code} - check if authentication needed"

                )



            if result["response_time_ms"] > 5000:

                result["recommendations"].append(

                    "Slow response - consider increasing timeout"

                )



        except requests.Timeout:

            result["error"] = "Request timeout"

            result["recommendations"].append("URL may be slow or unreachable")

        except Exception as e:

            result["error"] = str(e)



        return result



    def analyze_url_type(self, url: str) -> Dict:

        """

        Analyze what type of resource the URL points to.



        Args:

            url: URL to analyze



        Returns:

            Analysis result

        """

        analysis = {

            "url": url,

            "detected_type": "unknown",

            "is_api": False,

            "is_html": False,

            "requires_rendering": False,

            "has_captcha": False,

            "indicators": []

        }



        # Check URL pattern

        url_lower = url.lower()

        if any(pattern in url_lower for pattern in ["api/", "graphql", "/v1/", "/v2/"]):

            analysis["is_api"] = True

            analysis["detected_type"] = "api"

            analysis["indicators"].append("API path in URL")



        # Fetch and analyze content

        try:

            response = requests.get(

                url,

                timeout=10,

                headers={"User-Agent": "Mozilla/5.0"}

            )



            content_type = response.headers.get("content-type", "")



            if "application/json" in content_type:

                analysis["is_api"] = True

                analysis["detected_type"] = "api_json"

                analysis["indicators"].append("JSON content type")



            elif "text/html" in content_type:

                analysis["is_html"] = True

                analysis["detected_type"] = "html"



                html = response.text

                html_lower = html.lower()



                # Check for rendering requirements

                if any(indicator in html_lower for indicator in ["react", "vue", "angular", "data-react"]):

                    analysis["requires_rendering"] = True

                    analysis["indicators"].append("JavaScript framework detected")



                # Check for CAPTCHA

                if any(indicator in html_lower for indicator in ["captcha", "cloudflare", "challenge"]):

                    analysis["has_captcha"] = True

                    analysis["indicators"].append("CAPTCHA detected")



        except Exception as e:

            analysis["error"] = str(e)



        return analysis



    def extract_sample_data(self, url: str) -> Dict:

        """

        Extract sample data from URL for analysis.



        Args:

            url: URL to extract from



        Returns:

            Sample data

        """

        sample = {

            "url": url,

            "data": None,

            "data_type": None,

            "preview": None

        }



        try:

            response = requests.get(

                url,

                timeout=10,

                headers={"User-Agent": "Mozilla/5.0"}

            )



            content_type = response.headers.get("content-type", "")



            if "application/json" in content_type:

                sample["data_type"] = "json"

                try:

                    sample["data"] = response.json()

                    sample["preview"] = str(sample["data"])[:500]

                except:

                    pass



            elif "text/html" in content_type:

                sample["data_type"] = "html"

                sample["preview"] = response.text[:500]



                # Try to extract visible text

                try:

                    soup = BeautifulSoup(response.text, "html.parser")

                    text = soup.get_text(separator=" ", strip=True)

                    sample["preview"] = text[:500]

                except:

                    pass



        except Exception as e:

            sample["error"] = str(e)



        return sample



    def test_multiple_urls(self, urls: List[str]) -> List[Dict]:

        """

        Test multiple URLs at once.



        Args:

            urls: List of URLs to test



        Returns:

            List of test results

        """

        results = []



        for url in urls:

            accessibility = self.test_url_accessibility(url)



            if accessibility["is_accessible"]:

                analysis = self.analyze_url_type(url)

                accessibility.update({

                    "detected_type": analysis["detected_type"],

                    "is_api": analysis["is_api"],

                    "requires_rendering": analysis["requires_rendering"],

                    "has_captcha": analysis["has_captcha"]

                })



            results.append(accessibility)



        return results
