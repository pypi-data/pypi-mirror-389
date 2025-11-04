"""

Response Validator - Validate scraped data

"""



from typing import Any, Dict, List

from ..config.schema import DataType





class ResponseValidator:

    """Validate scraped responses match expected format"""



    @staticmethod

    def validate_response(

        data: Any,

        expected_type: DataType,

        expected_format: str

    ) -> Dict:

        """

        Validate response data.



        Args:

            data: Extracted data

            expected_type: Expected DataType

            expected_format: Expected format description



        Returns:

            Validation result

        """

        validation = {

            "is_valid": False,

            "actual_type": None,

            "issues": [],

            "warnings": []

        }



        # Determine actual type

        if data is None:

            validation["actual_type"] = "null"

            validation["issues"].append("Data is None")

            return validation



        elif isinstance(data, list):

            validation["actual_type"] = "list"

            if expected_type == DataType.SINGLE_VALUE:

                validation["issues"].append(

                    f"Expected single value, got list of {len(data)} items"

                )



        elif isinstance(data, dict):

            validation["actual_type"] = "object"

            if expected_type == DataType.SINGLE_VALUE:

                validation["issues"].append("Expected single value, got object")



        else:

            validation["actual_type"] = "single_value"

            if expected_type == DataType.LIST:

                validation["issues"].append("Expected list, got single value")

            elif expected_type == DataType.OBJECT:

                validation["issues"].append("Expected object, got single value")



        # Type-specific validation

        if validation["actual_type"] == expected_type.value or not validation["issues"]:

            validation["is_valid"] = True



            # Additional checks

            if isinstance(data, (int, float)):

                if data < 0:

                    validation["warnings"].append("Numeric value is negative")



            elif isinstance(data, str):

                if not data.strip():

                    validation["issues"].append("String is empty or whitespace")

                    validation["is_valid"] = False



            elif isinstance(data, list):

                if not data:

                    validation["warnings"].append("List is empty")

                elif len(data) > 10000:

                    validation["warnings"].append("List is very large (>10k items)")



        return validation



    @staticmethod

    def validate_against_sample(

        data: Any,

        sample_value: Any

    ) -> Dict:

        """

        Validate data against sample value.



        Args:

            data: Actual data

            sample_value: Expected sample



        Returns:

            Validation result

        """

        validation = {

            "matches_sample_type": False,

            "matches_sample_structure": False,

            "differences": []

        }



        # Type check

        if type(data) == type(sample_value):

            validation["matches_sample_type"] = True

        else:

            validation["differences"].append({

                "type": "type_mismatch",

                "expected": str(type(sample_value)),

                "actual": str(type(data))

            })



        # Structure check for dicts

        if isinstance(data, dict) and isinstance(sample_value, dict):

            data_keys = set(data.keys())

            sample_keys = set(sample_value.keys())



            if data_keys == sample_keys:

                validation["matches_sample_structure"] = True

            else:

                missing = sample_keys - data_keys

                extra = data_keys - sample_keys



                if missing:

                    validation["differences"].append({

                        "type": "missing_keys",

                        "keys": list(missing)

                    })

                if extra:

                    validation["differences"].append({

                        "type": "extra_keys",

                        "keys": list(extra)

                    })



        # Structure check for lists

        elif isinstance(data, list) and isinstance(sample_value, list):

            if data and sample_value:

                # Compare first item structure

                if type(data[0]) == type(sample_value[0]):

                    validation["matches_sample_structure"] = True

                else:

                    validation["differences"].append({

                        "type": "list_item_type_mismatch",

                        "expected": str(type(sample_value[0])),

                        "actual": str(type(data[0]))

                    })



        return validation



    @staticmethod

    def suggest_fixes(validation_result: Dict) -> List[str]:

        """

        Suggest fixes for validation issues.



        Args:

            validation_result: Result from validate_response



        Returns:

            List of fix suggestions

        """

        suggestions = []



        for issue in validation_result.get("issues", []):

            if "Expected single value, got list" in issue:

                suggestions.append(

                    "Add action method 'extract_first_item' to get single value from list"

                )



            elif "Expected list, got single value" in issue:

                suggestions.append(

                    "Update expected data_type to 'single_value' in config"

                )



            elif "Data is None" in issue:

                suggestions.append(

                    "Check if api_path or xpath is correct"

                )

                suggestions.append(

                    "Verify URL returns expected data"

                )



            elif "String is empty" in issue:

                suggestions.append(

                    "Check if extraction method (xpath/api_path) is correct"

                )



        return suggestions
