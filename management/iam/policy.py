import oci
import csv
import openpyxl
from openpyxl.styles import Font

def list_iam_users_and_groups():
    config = oci.config.from_file()
    identity_client = oci.identity.IdentityClient(config)
    tenancy_id = config["tenancy"]
    
    print("Fetching users...")
    users = identity_client.list_users(tenancy_id).data
    print("Fetching groups...")
    groups = identity_client.list_groups(tenancy_id).data
    print("Fetching policies...")
    policies = identity_client.list_policies(tenancy_id).data
    
    user_group_map = {}
    for group in groups:
        group_members = identity_client.list_user_group_memberships(compartment_id=tenancy_id, group_id=group.id).data
        for member in group_members:
            user_group_map.setdefault(member.user_id, []).append(group.name)
    
    print("Fetching user last login info...")
    auth_client = oci.identity.IdentityClient(config)
    
    # Create an Excel workbook
    workbook = openpyxl.Workbook()
    
    # Create IAM Users sheet
    user_sheet = workbook.active
    user_sheet.title = "IAM Users"
    user_headers = ["User Name", "User OCID", "Status", "Groups", "Last Login", "Remarks"]
    user_sheet.append(user_headers)
    
    # Apply bold font to headers
    for cell in user_sheet[1]:
        cell.font = Font(bold=True)

    row = 2  # Start from the second row (1st row has headers)

    for user in users:
        try:
            auth_response = auth_client.get_authentication_policy(user.id).data
            last_login = auth_response.lifecycle_state if auth_response else "N/A"
        except:
            last_login = "N/A"
        
        remarks = "Active" if user.lifecycle_state == "ACTIVE" else "Inactive/Disabled"
        groups = ", ".join(user_group_map.get(user.id, ["No Group"]))
        user_sheet.append([user.name, user.id, user.lifecycle_state, groups, last_login, remarks])
        row += 1

    print("Writing IAM policies...")
    
    # Create IAM Policies sheet
    policy_sheet = workbook.create_sheet(title="IAM Policies")
    policy_headers = ["Policy Name", "Statements", "Compartment ID"]
    policy_sheet.append(policy_headers)

    # Apply bold font to headers
    for cell in policy_sheet[1]:
        cell.font = Font(bold=True)

    row = 2  # Start from the second row

    for policy in policies:
        for statement in policy.statements:
            policy_sheet.append([policy.name, statement, policy.compartment_id])
            row += 1
    
    # Save the Excel file
    workbook.save("iam_audit_report.xlsx")
    print("IAM audit report saved to iam_audit_report.xlsx")

if __name__ == "__main__":
    list_iam_users_and_groups()

