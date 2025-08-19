import json
import pandas as pd
import subprocess
from datetime import datetime

def fetch_policies():
    try:
        # Hardcoded tenancy OCID
        hardcoded_tenancy_ocid = "ocid1.tenancy.oc1..aaaaaaaahu6kn4sx2enaokaum4fe2o3v5fvmfxqu7hacz6dqrwlvum4ii2sa"

        # Use the hardcoded tenancy OCID
        tenancy_ocid = hardcoded_tenancy_ocid

        print(f"Using Tenancy OCID: {tenancy_ocid}")

        # Fetch policies using OCI CLI
        print("Fetching policies using OCI CLI...")
        command = f"oci iam policy list --compartment-id {tenancy_ocid} --all"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            raise Exception(f"Error running OCI CLI command: {result.stderr}")

        # Parse the CLI output
        policies_data = json.loads(result.stdout)
        return policies_data.get('data', []), tenancy_ocid

    except Exception as e:
        print(f"An error occurred: {e}")
        return [], None

def process_policies(policies):
    try:
        # Extract policy details
        policy_list = []
        for policy in policies:
            for statement in policy.get('statements', []):
                policy_list.append({
                    "Policy Name": policy.get('name', 'N/A'),
                    "Compartment ID": policy.get('compartment-id', 'N/A'),
                    "Statement": statement,
                    "Lifecycle State": policy.get('lifecycle-state', 'N/A'),
                    "Time Created": policy.get('time-created', 'N/A')
                })

        # Convert to DataFrame
        df = pd.DataFrame(policy_list)
        return df

    except Exception as e:
        print(f"Error processing policies: {e}")
        return pd.DataFrame()

def save_files(df, tenancy_ocid):
    try:
        # Get current date for the file name
        current_date = datetime.now().strftime("%Y-%m-%d")
        tenancy_name = tenancy_ocid.split(".")[1] if tenancy_ocid else "unknown"

        # Generate file names with dynamic titles
        csv_file = f"tenancy_policies_{tenancy_name}_{current_date}.csv"
        excel_file = f"tenancy_policies_{tenancy_name}_{current_date}.xlsx"

        # Save as CSV
        df.to_csv(csv_file, index=False)
        print(f"CSV file saved: {csv_file}")

        # Save as Excel
        df.to_excel(excel_file, index=False)
        print(f"Excel file saved: {excel_file}")

    except Exception as e:
        print(f"Error saving files: {e}")

def main():
    print("Starting policy export process...")
    policies, tenancy_ocid = fetch_policies()
    if not policies:
        print("No policies found or unable to fetch policies. Exiting.")
        return

    df = process_policies(policies)
    if df.empty:
        print("No policy data to export. Exiting.")
        return

    save_files(df, tenancy_ocid)
    print("Policy export completed successfully!")

if __name__ == "__main__":
    main()
