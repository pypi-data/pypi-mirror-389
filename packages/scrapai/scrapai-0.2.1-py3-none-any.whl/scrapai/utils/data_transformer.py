"""

Data Transformer - Transform and clean extracted data

"""



import re

import json

from typing import Any, Optional, Callable

from decimal import Decimal

from datetime import datetime, timedelta





class DataTransformer:

    """Transform and clean scraped data"""



    def extract_from_json_path(

        self,

        data: Any,

        path: str,

        default: Any = None,

        filter_func: Optional[Callable] = None

    ) -> Any:

        """

        Extract value from JSON using dot-notation path with advanced features.

        Supports: first, last, second, second_last, length, filter, sort, reverse.

        Based on deep_access from daap-esg.



        Args:

            data: JSON data (dict/list)

            path: Dot-notation path (e.g., "data.last.second", "items.first.value")

            default: Default value if path not found

            filter_func: Optional filter function for arrays



        Returns:

            Extracted value

        """

        if not path:

            return data



        # Convert string to list if needed

        if isinstance(path, str):

            keys = path.split(".")

        else:

            keys = path



        if not keys:

            return data



        key = keys[0]

        remaining_keys = keys[1:]



        # Handle special dict keys

        if isinstance(data, dict):

            if key == "value":

                # Get first key's value

                dict_keys = list(data.keys())

                if dict_keys:

                    value = data.get(dict_keys[0], default)

                else:

                    value = default

            elif key == "kvalue":

                value = data.get("value", default)

            else:

                value = data.get(key, default)



        # Handle lists with special keywords

        elif isinstance(data, list):

            try:

                if key == "reverse":

                    value = data[::-1]

                elif key == "sort":

                    if remaining_keys:

                        sort_key = remaining_keys[0]

                        sort_order = remaining_keys[1] if len(remaining_keys) > 1 else "asc"

                        if sort_order == "asc":

                            value = sorted(data, key=lambda x: x.get(sort_key) if isinstance(x, dict) else x)

                        else:

                            value = sorted(data, key=lambda x: x.get(sort_key) if isinstance(x, dict) else x, reverse=True)  # noqa: C0301

                        remaining_keys = remaining_keys[2:]

                    else:

                        value = data

                elif key == "filter" and filter_func is None and len(remaining_keys) >= 2:

                    # Filter by date (e.g., filter.date_key.days)

                    date_key = remaining_keys[0]

                    filter_date_key_days = int(remaining_keys[1])

                    current_date = (datetime.now() - timedelta(days=filter_date_key_days)).strftime('%Y-%m-%d')

                    value = [row for row in data if isinstance(row, dict) and current_date in str(row.get(date_key, ""))]  # noqa: C0301

                    remaining_keys = remaining_keys[2:]

                elif key == "length":

                    value = len(data)

                elif key == "first":

                    value = data[0] if data else default

                elif key == "second":

                    value = data[1] if len(data) > 1 else default

                elif key == "last":

                    value = data[-1] if data else default

                elif key == "second_last":

                    value = data[-2] if len(data) > 1 else default

                elif key == "filter" and filter_func is not None:

                    value = [item for item in data if filter_func(item)]

                else:

                    # Try numeric index

                    try:

                        index = int(key)

                        value = data[index]

                    except (ValueError, IndexError):

                        # Try recursive access on each item

                        value = default

            except (IndexError, KeyError, TypeError):

                value = default



        # Handle other types

        elif key == "parse_json":

            try:

                value = json.loads(data)

            except (json.JSONDecodeError, TypeError):

                value = data

        else:

            # Try attribute access

            value = getattr(data, key, default)



        # Recursively process remaining keys

        if remaining_keys:

            return self.extract_from_json_path(value, remaining_keys, default, filter_func)



        return value



    def extract_numeric_value(self, value: Any) -> Optional[float]:

        """

        Extract numeric value from string/mixed data.



        Args:

            value: Input value (string, number, etc.)



        Returns:

            Float value or None

        """

        if isinstance(value, (int, float)):

            return float(value)



        if isinstance(value, str):

            # Remove common non-numeric characters

            cleaned = re.sub(r'[,$\s]', '', value)



            # Find number pattern

            match = re.search(r'-?\d+\.?\d*', cleaned)

            if match:

                try:

                    return float(match.group())

                except:

                    pass



        return None



    def extract_text_content(self, value: Any) -> str:

        """

        Extract text content, removing HTML tags and extra whitespace.



        Args:

            value: Input value



        Returns:

            Clean text string

        """

        if value is None:

            return ""



        text = str(value)



        # Remove HTML tags

        text = re.sub(r'<[^>]+>', '', text)



        # Normalize whitespace

        text = ' '.join(text.split())



        return text.strip()



    def convert_k_m_b_to_number(self, value: Any) -> Optional[float]:

        """

        Convert K/M/B notation to full number.

        Examples: "1.5K" -> 1500, "2.3M" -> 2300000



        Args:

            value: Value with K/M/B suffix



        Returns:

            Full number

        """

        if isinstance(value, (int, float)):

            return float(value)



        if not isinstance(value, str):

            value = str(value)



        value = value.strip().upper()



        multipliers = {

            'K': 1_000,

            'M': 1_000_000,

            'B': 1_000_000_000,

            'T': 1_000_000_000_000

        }



        for suffix, multiplier in multipliers.items():

            if value.endswith(suffix):

                try:

                    number = float(value[:-1])

                    return number * multiplier

                except:

                    pass



        # Try to parse as regular number

        try:

            return float(value.replace(',', ''))

        except:

            return None



    def convert_to_int(self, value: Any) -> Optional[int]:

        """Convert value to integer."""

        try:

            if isinstance(value, str):

                # Remove commas and whitespace

                value = value.replace(',', '').strip()

            return int(float(value))

        except:

            return None



    def convert_to_float(self, value: Any) -> Optional[float]:

        """Convert value to float."""

        try:

            if isinstance(value, str):

                value = value.replace(',', '').strip()

            return float(value)

        except:

            return None



    def calculate_tps_from_transactions(self, total_transactions: Any, time_window_seconds: int = 86400) -> Optional[float]:  # noqa: C0301

        """

        Calculate transactions per second.



        Args:

            total_transactions: Total transaction count

            time_window_seconds: Time window (default: 86400 = 24 hours)



        Returns:

            TPS value

        """

        try:

            tx_count = float(total_transactions)

            return tx_count / time_window_seconds

        except:

            return None



    def parse_timestamp(self, value: Any, fmt: str = "%Y-%m-%dT%H:%M:%S") -> Optional[datetime]:

        """

        Parse timestamp string to datetime.



        Args:

            value: Timestamp string

            format: Expected format



        Returns:

            datetime object

        """

        if isinstance(value, datetime):

            return value



        if isinstance(value, (int, float)):

            # Unix timestamp

            try:

                return datetime.fromtimestamp(value)

            except:

                pass



        if isinstance(value, str):

            try:

                return datetime.strptime(value, fmt)

            except:

                # Try ISO format

                try:

                    return datetime.fromisoformat(value.replace('Z', '+00:00'))

                except:

                    pass



        return None



    def clean_whitespace(self, value: Any) -> str:

        """

        Clean and normalize whitespace.



        Args:

            value: Input value



        Returns:

            Cleaned string

        """

        if value is None:

            return ""



        text = str(value)

        return ' '.join(text.split())



    def extract_first_item(self, value: Any) -> Any:

        """

        Extract first item from list.



        Args:

            value: Input value (should be list)



        Returns:

            First item or original value

        """

        if isinstance(value, list) and value:

            return value[0]

        return value



    def extract_last_item(self, value: Any) -> Any:

        """

        Extract last item from list.



        Args:

            value: Input value (should be list)



        Returns:

            Last item or original value

        """

        if isinstance(value, list) and value:

            return value[-1]

        return value



    def sum_list_values(self, value: Any) -> Optional[float]:

        """

        Sum all numeric values in a list.



        Args:

            value: List of numbers



        Returns:

            Sum

        """

        if not isinstance(value, list):

            return None



        try:

            return sum(float(v) for v in value if v is not None)

        except:

            return None



    def filter_last_24_hours(self, items: list, timestamp_key: str = "timestamp") -> list:

        """

        Filter list to items from last 24 hours.



        Args:

            items: List of dicts with timestamps

            timestamp_key: Key containing timestamp



        Returns:

            Filtered list

        """

        if not isinstance(items, list):

            return []



        cutoff = datetime.utcnow() - timedelta(hours=24)

        filtered = []



        for item in items:

            if isinstance(item, dict) and timestamp_key in item:

                ts = self.parse_timestamp(item[timestamp_key])

                if ts and ts >= cutoff:

                    filtered.append(item)



        return filtered



    def filter_yesterday(self, items: list, timestamp_key: str = "timestamp") -> list:

        """

        Filter list to items from yesterday.



        Args:

            items: List of dicts with timestamps

            timestamp_key: Key containing timestamp



        Returns:

            Filtered list

        """

        if not isinstance(items, list):

            return []



        today = datetime.utcnow().date()

        yesterday = today - timedelta(days=1)

        filtered = []



        for item in items:

            if isinstance(item, dict) and timestamp_key in item:

                ts = self.parse_timestamp(item[timestamp_key])

                if ts and ts.date() == yesterday:

                    filtered.append(item)



        return filtered
