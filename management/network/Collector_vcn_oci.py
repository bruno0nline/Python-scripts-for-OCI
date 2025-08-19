import oci
import json

# Load the configuration
config = oci.config.from_file("~/.oci/config")

# Initialize clients
virtual_network_client = oci.core.VirtualNetworkClient(config)
identity_client = oci.identity.IdentityClient(config)

# Get tenancy ID from the config
tenancy_id = config["tenancy"]

# List to store VCN details
vcn_details = []

try:
    # List all compartments
    compartments = oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        tenancy_id,
        compartment_id_in_subtree=True,  # Enable fetching sub-compartments
        access_level="ANY"  # Include all compartments the user has access to
    ).data

    # Include the root compartment
    compartments.append(oci.identity.models.Compartment(id=tenancy_id, name="Tenancy Root"))

    # Iterate through compartments and fetch VCNs
    for compartment in compartments:
        if compartment.lifecycle_state == "ACTIVE":
            print(f"Listing VCNs in compartment: {compartment.name}")
            vcn_response = oci.pagination.list_call_get_all_results(
                virtual_network_client.list_vcns,
                compartment_id=compartment.id
            )
            for vcn in vcn_response.data:
                print(f"VCN Name: {vcn.display_name}, VCN ID: {vcn.id}")
                # Add VCN details to the list
                vcn_details.append({
                    "compartment": compartment.name,
                    "vcn_name": vcn.display_name,
                    "vcn_id": vcn.id,
                    "region": config["region"]  # Add region info
                })

    # Export VCN details to a JSON file
    with open("vcn_details.json", "w") as file:
        json.dump(vcn_details, file, indent=4)

    print("VCN details have been exported to 'vcn_details.json'.")

except oci.exceptions.ServiceError as e:
    print(f"Service Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}")
