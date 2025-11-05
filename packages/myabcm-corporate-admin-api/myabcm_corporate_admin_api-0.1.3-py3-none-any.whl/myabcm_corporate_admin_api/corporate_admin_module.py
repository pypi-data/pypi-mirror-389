from datetime import datetime
from typing import List, Dict, Any

import requests

# --------------------------------------------------------------------------------------
# Constants declaration

OPERATION_SCHEDULED = 0
OPERATION_IN_PROGRESS = 1
OPERATION_ABORTING = 2
OPERATION_FINISHED = 3
OPERATION_ABORTED = 4

SEPARATOR_CONSTANT = "\r\r\r\n\r\r\r"

API_VERSION = "v2"


# --------------------------------------------------------------------------------------
# CorporateAdmin class

class CorporateAdmin:
    """
    Client for interacting with the Corporate Admin API.

    This class provides methods to manage organizations and users within the
    corporate system, including authentication, creation, removal, and password
    management.
    """
    def __init__(self, base_url, login_name, password, console_feedback=True):
        self.__base_url = base_url
        self.__login_name = login_name
        self.__password = password
        self.__logged_username = ""
        self.__session_token = ""
        self.__console_feedback = console_feedback

    @staticmethod
    def __status_code_ok(status_code):
        """
        Checks if the HTTP status code indicates a successful response (2xx).

        Parameters:
            status_code (int): The HTTP status code to check.

        Returns:
            bool: True if the status code is between 200 and 299, False otherwise.
        """
        if 200 <= status_code <= 299:
            return True
        else:
            return False

    def __get_default_headers(self):
        """
        Constructs the default HTTP headers for API requests, including authorization.

        Returns:
            dict: A dictionary containing the 'Authorization' and 'Content-Type' headers.
        """
        # Set headers with authorization
        headers = {
            "Authorization": f"Bearer {self.__session_token}",
            "Content-Type": "application/json"
        }
        return headers

    # def __read_user_import_excel(self, filename, sheet_name= "User Data"):
    #     try:
    #         workbook = openpyxl.load_workbook(filename)
    #         sheet = workbook[sheet_name]
    #     except FileNotFoundError:
    #         raise FileNotFoundError(f"File {filename} not found.")
    #         return []
    #     except KeyError:
    #         raise FileNotFoundError(f"Sheet {sheet_name} not found in {filename}.")
    #         return []
    #     users_data =[]
    #     headers = [cell.value for cell in sheet[1]]
    #
    #     column_mapping = {
    #         "OrganizationName": "OrganizationName",
    #         "UserName": "UserName",
    #         "FullName": "FullName",
    #         "Password": "Password",
    #         "SalaryFactor": "SalaryFactor",
    #         "Email": "Email",
    #         "Phone": "Phone",
    #         "SiteSessionTimeout": "SiteSessionTimeout",
    #         "PasswordDuration": "PasswordDuration",
    #         "RoleType": "RoleType",
    #         "IsExternalUser": "IsExternalUser",
    #         "UseSsoOnly": "UseSsoOnly",
    #         "UserEnabled": "UserEnabled",
    #         "ExpirationDate": "ExpirationDate",
    #         "DefaultIdiomId": "DefaultIdiomId",
    #         "TimeZoneId": "TimeZoneId",
    #         "CanCreateModel": "CanCreateModel",
    #         "PasswordRetriesAllowed": "PasswordRetriesAllowed",
    #         "NamedLicense": "NamedLicense",
    #         "PrivateSpace": "PrivateSpace",
    #         "ComponentAccessModeling": "ComponentAccessModeling",
    #         "ComponentAccessIntegration": "ComponentAccessIntegration",
    #         "ComponentAccessAnalysis": "ComponentAccessAnalysis",
    #         "ComponentAccessSurveys": "ComponentAccessSurveys",
    #         "ComponentAccessSmartMetrics": "ComponentAccessSmartMetrics",
    #         "UserGroupIds": "UserGroupIds",
    #         "ChangePasswordNextLogon": "ChangePasswordNextLogon"
    #     }
    #     for row_index in range(2, sheet.max_row + 1):
    #         user_info = {}
    #         for col_index, header_excel in enumerate(headers):
    #             cell_value = sheet.cell(row=row_index, column=col_index + 1).value
    #             api_key = column_mapping.get(header_excel, header_excel)
    #             if api_key in ["SalaryFactor", "SiteSessionTimeout", "PasswordDuration",
    #                            "RoleType", "DefaultIdiomId", "PasswordRetriesAllowed", "PrivateSpace"]:
    #                 try:
    #                     user_info[api_key] = int(cell_value) if cell_value is not None else 0
    #                 except (ValueError, TypeError):
    #                     user_info[api_key] = 0
    #             elif api_key in ["IsExternalUser", "UseSsoOnly", "UserEnabled", "CanCreateModel",
    #                              "ComponentAccessModeling", "ComponentAccessIntegration",
    #                              "ComponentAccessAnalysis", "ComponentAccessSurveys",
    #                              "ComponentAccessSmartMetrics", "ChangePasswordNextLogon"]:
    #                 user_info[api_key] = str(cell_value).lower() == 'true' if cell_value is not None else False
    #             elif api_key == "ExpirationDate":
    #                 if isinstance(cell_value, datetime):
    #                     user_info[api_key] = cell_value.isoformat(timespec='milliseconds') + 'Z'
    #                 elif isinstance(cell_value, str):
    #                     try:
    #                         dt_obj = datetime.fromisoformat(cell_value.replace('Z', '+00:00'))
    #                         user_info[api_key] = dt_obj.isoformat(timespec='milliseconds') + 'Z'
    #                     except ValueError:
    #                         user_info[api_key] = None
    #                 else:
    #                     user_info[api_key] = None
    #             elif api_key == "UserGroupIds":
    #                 if isinstance(cell_value, str) and cell_value:
    #                     try:
    #                         user_info[api_key] = [int(id_str.strip()) for id_str in cell_value.split(';') if
    #                                               id_str.strip()]
    #                     except ValueError:
    #                         user_info[api_key] = [0]
    #                 else:
    #                     user_info[api_key] = [0]
    #             else:
    #                 user_info[api_key] = cell_value if cell_value is not None else ""
    #
    #         users_data.append(user_info)
    #         return users_data

    def __get_organization(self):
        """
        Retrieves a list of all organizations from the API.

        Returns:
            list: A list of dictionaries, each representing an organization.
        """
        #Set URL
        url = f"{self.__base_url}/{API_VERSION}/admin/organizations"

        #Make GET request
        response = requests.get(url, headers=self.__get_default_headers())

        #Check response
        if CorporateAdmin.__status_code_ok(response.status_code):
            data = response.json()
            return data
        else:
        # If organization not found, generate exception
            raise Exception(f"Error getting organizations (Status code: {response.status_code})")

    def __get_organization_id(self, organization_reference):
        """
        Retrieves the ID of an organization based on its description (reference).

        Parameters:
            organization_reference (str): The description of the organization to find.

        Returns:
            int: The ID of the found organization.
        """
        #Get organizations
        organizations = self.__get_organization()

        #Search for desired organization (and return its ID if found)
        for organization in organizations:
            if organization.get("Description") == organization_reference:
                return organization.get("Id")

        #Generate exception if it's not found
        raise Exception(f"Organization reference ({organization_reference}) not found")

    def __get_users(self, organization_id):
        """
        Retrieves a list of users for a specific organization.

        Parameters:
            organization_id (int): The ID of the organization to retrieve users from.

        Returns:
            list: A list of dictionaries, each representing a user.
        """
        #Set URL
        url = f"{self.__base_url}/{API_VERSION}/admin/organizations/{organization_id}/users"

        #Make GET request
        response = requests.get(url, headers=self.__get_default_headers())

        #Check response
        if CorporateAdmin.__status_code_ok(response.status_code):
            data = response.json()
            return data
        else:
        #Generate exception if user not found
            raise Exception(f"Error getting users (Status code: {response.status_code})")

    def __get_user_id(self, organization_name, username):
        """
        Retrieves the ID of a user based on their organization name and email.

        Parameters:
            organization_name (str): The name of the organization the user belongs to.
            username (str): The username of the user to find.

        Returns:
            int: The ID of the found user.
        """
        #Get Organizations
        organization_id = self.__get_organization_id(organization_name)

        #Get Users
        users = self.__get_users(organization_id)

        #Search for desired user (and return its ID if found)
        for user in users:
            if user.get("Name") == username:
                return user.get("Id")

        #Generate exception if the user cannot be found
        raise Exception(f"Username ({username}) not found")

    def logon(self):
        """
        Authenticates with the Corporate Admin API using the provided login credentials.

        This method sets the internal session token upon successful authentication,
        which is then used for subsequent API calls.
        """
        if self.__console_feedback: print(f"Logging on to {self.__base_url} using user {self.__login_name}...",
                                          end="")
        #Set URL
        url = f"{self.__base_url}/{API_VERSION}/admin/logon"

        #Set Body parameters
        body = {"Username": self.__login_name, "Password": self.__password, "ClientIPAddress": "192.0.0.1"}

        #Make POST request
        response = requests.post(url, json=body)

        #Check response
        if CorporateAdmin.__status_code_ok(response.status_code):
            data = response.json()
            if data.get("Result") == 0:
                #Login successful, store session token
                self.__session_token = data.get("SessionToken")
                if self.__console_feedback: print("ok")

            else:
                if self.__console_feedback: print("failed")
                #Login failed, generate custom exception based on result code
                if data.get("Result") == 6:
                    raise Exception("Error logging in (Password expired)")
                if data.get("Result") == 7:
                    raise Exception("Error logging in (Product not authorized)")
                if data.get("Result") == 8:
                    raise Exception("Error logging in (License not available)")
                if data.get("Result") == 9:
                    raise Exception("Error logging in (User not authorized expired)")
                raise Exception(f"Error logging in (Logon result code: {data.get('Result')})")
        else:
            #Result code not in 6 to 9 range, generate generic exception with result code
            raise Exception(f"Error logging in (Status code: {response.status_code})")

    def create_organization(self, organization_name: str):
        """
        Creates a new organization in the corporate system.

        Parameters:
            organization_name (str): The descriptive name for the new organization.
        """
        if self.__console_feedback: print(f"Creating organization: {organization_name}...")
        # Set URL
        url = f"{self.__base_url}/{API_VERSION}/admin/organizations"

        # Set Body parameters
        body = {"Description": organization_name}

        # Make POST request
        response = requests.post(url, json=body, headers=self.__get_default_headers())

        # Check response
        if not CorporateAdmin.__status_code_ok(response.status_code):
            if self.__console_feedback: print(f"Failed")
            raise Exception(f"Failed to create organization (Status code: {response.status_code})")

        else:
            if self.__console_feedback: print("ok")

    def remove_organization(self, organization_name: str):
        """
        Removes an existing organization from the corporate system.

        Parameters:
            organization_name (str): The descriptive name of the organization to remove.
        """
        if self.__console_feedback: print(f"Removing organization: {organization_name}...")
        # Get organization ID
        organization_id = self.__get_organization_id(organization_name)

        # Set URL
        url = f"{self.__base_url}/{API_VERSION}/admin/organizations/{organization_id}"

        # Make DELETE request
        response = requests.delete(url, headers=self.__get_default_headers())

        # Check response
        if not CorporateAdmin.__status_code_ok(response.status_code):
            if self.__console_feedback: print(f"Failed")
            raise Exception(f"Failed to remove organization (Status code: {response.status_code})")
        else:
            if self.__console_feedback: print("ok")

    def create_users(self, organization_reference: str, users_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Creates multiple users within a specified organization.

        Iterates through a list of user data dictionaries, attempts to create each user
        via the API, and collects the results for each operation. Handles potential
        connection errors and API response errors.

        Parameters:
            organization_reference (str): The descriptive name of the organization
                                          where users will be created.
            users_data (List[Dict[str, Any]]): A list of dictionaries, where each
                                                dictionary contains the data for a user
                                                to be created.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing the outcome
                                  of a user creation attempt. Each dictionary includes:
                                  - 'username' (str): The username of the user attempted.
                                  - 'status' (str): 'success' or 'failed'.
                                  - 'status_code' (int/None): The HTTP status code of the response.
                                  - 'response' (dict/str): The JSON response body on success,
                                                            or raw text/error message on failure.
                                  - 'error_message' (str, optional): A description of the error if failed.
        """

        # Initialize results list
        results = []
        try:
            # Get organization ID
            organization_id = self.__get_organization_id(organization_reference)
            if self.__console_feedback: print(f"Found organization: {organization_id}...")

        except Exception as e:
            # Raise exception if organization not found
            raise Exception(f"Can't find organization: {organization_reference}") from e
        # Set URL
        url = f"{self.__base_url}/{API_VERSION}/admin/organizations/{organization_id}/users"

        # Iterate over user data
        for user_data in users_data:
            # Get username from user data
            username = user_data.get("Username")
            if self.__console_feedback: print(f"Creating user: {username}...")

            # Ensure ExpirationDate is in the correct ISO 8601 format with 'Z'
            if isinstance(user_data.get("ExpirationDate"), datetime):
                user_data["ExpirationDate"] = user_data["ExpirationDate"].isoformat(timespec="milliseconds") + "Z"
            elif "ExpirationDate" in user_data and user_data["ExpirationDate"] and not user_data[
                "ExpirationDate"].endswith("Z"):
                user_data["ExpirationDate"] += "Z"

            try:
                # Make POST request
                response = requests.post(url, json=user_data, headers=self.__get_default_headers())
                if CorporateAdmin.__status_code_ok(response.status_code):
                    if self.__console_feedback: print(f"User {username} created!")

                    # Append success result
                    results.append({
                        "username": username,
                        "status": "success",
                        "status_code": response.status_code,
                        "response": response.json()
                    })

                else:
                    if self.__console_feedback: print(f"User {username} failed!")
                    # Append failed result
                    results.append({
                        "username": username,
                        "status": "failed",
                        "status_code": response.status_code,
                        "response": response.text
                    })
            except requests.exceptions.RequestException as e:
                # Set error message for request exceptions
                error_msg = f"Connection/Request Error for user {username}: {e}"
                if self.__console_feedback: print(f"  {error_msg}")
                # Append failed result with error message
                results.append({
                    "username": username,
                    "status": "failed",
                    "status_code": None,
                    "error_message": error_msg,
                    "response": "N/A - Connection Error"
                })
            except Exception as e:
                # Set error message for unexpected exceptions
                error_msg = f"An unexpected error occurred for user {username}: {e}"
                if self.__console_feedback: print(f"  {error_msg}")
                # Append failed result with error message
                results.append({
                    "username": username,
                    "status": "failed",
                    "status_code": None,
                    "error_message": error_msg,
                    "response": "N/A - Unexpected Error"
                })

        return results

    def reset_user_password(self, organization: str, username: str, password: str):
        """
        Resets the password for a specific user within an organization.

        Parameters:
            organization (str): The descriptive name of the organization the user belongs to.
            username (str): The user address of the user whose password will be reset.
            password (str): The new password for the user.
        """
        if self.__console_feedback: print(f"Resetting user: {username}...")

        # Get organization ID
        organization_id = self.__get_organization_id(organization)

        # Get user ID
        user_id = self.__get_user_id(organization, username)

        # Set URL
        url = f"{self.__base_url}/{API_VERSION}/admin/organizations/{organization_id}/users/{user_id}/update-password"

        # Set Body parameters
        body = {"Password": password}

        # Make PUT request
        response = requests.put(url, json=body, headers=self.__get_default_headers())

        # Check response
        if not CorporateAdmin.__status_code_ok(response.status_code):
            if self.__console_feedback: print(f"Failed")
            raise Exception(f"Failed to update user (Status code: {response.status_code})")
        else:
            if self.__console_feedback: print("ok")

    def reset_user(self, organization_reference: str, users_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resets (updates) the data for multiple users within an organization.

        Iterates over a list of user data dictionaries, attempts to update each user
        via the API, and collects the results for each operation. Handles potential
        connection errors and API response errors.

        Parameters:
            organization_reference (str): The descriptive name of the organization
                                          where users will be reset/updated.
            users_data (List[Dict[str, Any]]): A list of dictionaries, where each
                                                dictionary contains the data for a user
                                                to be updated. Must include the 'Username'
                                                to identify the user.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing the outcome
                                  of a user reset/update attempt. Each dictionary includes:
                                  - 'username' (str): The username of the user attempted.
                                  - 'status' (str): 'success' or 'failed'.
                                  - 'status_code' (int/None): The HTTP status code of the response.
                                  - 'response' (dict/str): The JSON response body on success,
                                                            or raw text/error message on failure.
                                  - 'error_message' (str, optional): A description of the error if failed.
        """
        # Initialize results list
        results = []
        try:
            # Get organization ID
            organization_id = self.__get_organization_id(organization_reference)
            # Print console feedback
            if self.__console_feedback: print(f"Found organization: {organization_id}...")
        except Exception as e:
            # Raise exception if organization not found
            raise Exception(f"Can't find organization: {organization_reference}") from e

        # Iterate over user data
        for user_data in users_data:
            # Get username from user data
            username = user_data.get("Username")
            # Check if username is missing
            if not username:
                # Append failed result for missing username
                results.append({
                    "username": "N/A",
                    "status": "failed",
                    "status_code": None,
                    "error_message": "User data missing 'Username' for reset.",
                    "response": "N/A"
                })
                # Continue to next user
                continue

            # Print console feedback
            if self.__console_feedback: print(f"Attempting to reset user: {username}...", end="")
            try:
                # Get user ID
                user_id = self.__get_user_id(organization_reference, username)
            except Exception as e:
                # Set error message if user not found
                error_msg = f"Can't find user {username} in organization {organization_reference}: {e}"
                # Print console feedback
                if self.__console_feedback: print(f"  {error_msg}")
                # Append failed result
                results.append({
                    "username": username,
                    "status": "failed",
                    "status_code": None,
                    "error_message": error_msg,
                    "response": "N/A - User Not Found"
                })
                # Continue to next user
                continue

            # Set URL
            url = f"{self.__base_url}/{API_VERSION}/admin/organizations/{organization_id}/users/{user_id}"

            try:
                # Make PUT request
                response = requests.put(url, json=user_data, headers=self.__get_default_headers())
                # Check response
                if CorporateAdmin.__status_code_ok(response.status_code):
                    # Print console feedback
                    if self.__console_feedback: print(f"ok")
                    # Append success result
                    results.append({
                        "username": username,
                        "status": "success",
                        "status_code": response.status_code,
                        "response": response.json()
                    })
                else:
                    # Print console feedback
                    if self.__console_feedback: print(f"failed")
                    # Append failed result
                    results.append({
                        "username": username,
                        "status": "failed",
                        "status_code": response.status_code,
                        "response": response.text
                    })
            except Exception as e:
                # Set error message for unexpected exceptions
                error_msg = f"An unexpected error occurred for user {username}: {e}"
                # Print console feedback
                if self.__console_feedback: print(f"{error_msg}")
                # Append failed result with error message
                results.append({
                    "username": username,
                    "status": "failed",
                    "status_code": None,
                    "error_message": error_msg,
                    "response": "N/A - Unexpected Error"
                })
        # Return results
        return results

