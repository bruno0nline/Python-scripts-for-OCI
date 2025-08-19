import oci
import json
import csv
from oci.object_storage import UploadManager
import argparse

# Load the configuration
config = oci.config.from_file("~/.oci/config")

# Initialize clients
identity_client = oci.identity.IdentityClient(config)
virtual_network_client = oci.core.VirtualNetworkClient(config)
compute_client = oci.core.ComputeClient(config)
block_storage_client = oci.core.BlockstorageClient(config)
object_storage_client = oci.object_storage.ObjectStorageClient(config)
database_client = oci.database.DatabaseClient(config)
load_balancer_client = oci.load_balancer.LoadBalancerClient(config)

# Get tenancy ID
tenancy_id = config["tenancy"]
namespace = object_storage_client.get_namespace().data

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Discover OCI Resources")
parser.add_argument("--type", help="Filter by resource type (e.g., vcn, compute, block)")
parser.add_argument("--compartment-name", help="Filter by compartment name")
args = parser.parse_args()

# Initialize result storage
resources = {}

try:
    # Fetch all compartments (including root compartment)
    compartments = oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ANY"
    ).data
    compartments.append(oci.identity.models.Compartment(id=tenancy_id, name="Tenancy Root"))

    # Iterate through compartments
    for compartment in compartments:
        if compartment.lifecycle_state == "ACTIVE":
            if args.compartment_name and args.compartment_name != compartment.name:
                continue

            print(f"Discovering resources in compartment: {compartment.name}")
            resources[compartment.name] = {}

            # Discover VCNs
            if not args.type or args.type == "vcn":
                vcn_response = oci.pagination.list_call_get_all_results(
                    virtual_network_client.list_vcns,
                    compartment_id=compartment.id
                ).data
                resources[compartment.name]["VCNs"] = [{"name": vcn.display_name, "id": vcn.id} for vcn in vcn_response]

            # Discover Compute Instances
            if not args.type or args.type == "compute":
                instance_response = oci.pagination.list_call_get_all_results(
                    compute_client.list_instances,
                    compartment_id=compartment.id
                ).data
                resources[compartment.name]["Compute Instances"] = [
                    {"name": instance.display_name, "id": instance.id} for instance in instance_response
                ]

            # Discover Block Volumes
            if not args.type or args.type == "block":
                volume_response = oci.pagination.list_call_get_all_results(
                    block_storage_client.list_volumes,
                    compartment_id=compartment.id
                ).data
                resources[compartment.name]["Block Volumes"] = [
                    {"name": volume.display_name, "id": volume.id} for volume in volume_response
                ]

            # Discover Object Storage Buckets
            if not args.type or args.type == "bucket":
                bucket_response = oci.pagination.list_call_get_all_results(
                    object_storage_client.list_buckets,
                    namespace_name=namespace,
                    compartment_id=compartment.id
                ).data
                resources[compartment.name]["Buckets"] = [
                    {"name": bucket.name} for bucket in bucket_response
                ]

                # List objects in buckets
                for bucket in bucket_response:
                    object_response = oci.pagination.list_call_get_all_results(
                        object_storage_client.list_objects,
                        namespace_name=namespace,
                        bucket_name=bucket.name
                    ).data
                    resources[compartment.name]["Bucket Objects"] = [
                        {"bucket_name": bucket.name, "object_name": obj.name} for obj in object_response.objects
                    ]

            # Discover Autonomous Databases
            if not args.type or args.type == "adb":
                adb_response = oci.pagination.list_call_get_all_results(
                    database_client.list_autonomous_databases,
                    compartment_id=compartment.id
                ).data
                resources[compartment.name]["Autonomous Databases"] = [
                    {"name": adb.display_name, "id": adb.id} for adb in adb_response
                ]

            # Discover Load Balancers
            if not args.type or args.type == "lb":
                lb_response = oci.pagination.list_call_get_all_results(
                    load_balancer_client.list_load_balancers,
                    compartment_id=compartment.id
                ).data
                resources[compartment.name]["Load Balancers"] = []
                for lb in lb_response:
                    lb_details = load_balancer_client.get_load_balancer(lb.id).data
                    resources[compartment.name]["Load Balancers"].append({
                        "name": lb.display_name,
                        "id": lb.id,
                        "shape": lb.shape_name,
                        "subnets": lb_details.subnet_ids
                    })

    # Export resources to a JSON file
    with open("oci_resources.json", "w") as file:
        json.dump(resources, file, indent=4)

    print("Resource discovery completed. Results saved to 'oci_resources.json'.")

    # Generate a summary report
    summary = {}
    for compartment, resource_types in resources.items():
        for resource_type, resource_list in resource_types.items():
            summary[resource_type] = summary.get(resource_type, 0) + len(resource_list)

    # Print the summary
    print("Resource Summary:")
    for resource_type, count in summary.items():
        print(f"{resource_type}: {count}")

    # Save the summary to a JSON file
    with open("oci_resource_summary.json", "w") as summary_file:
        json.dump(summary, summary_file, indent=4)

    # Export compute instances to a CSV file
    with open("compute_instances.csv", "w", newline="") as csvfile:
        fieldnames = ["Compartment", "Name", "ID"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for compartment, data in resources.items():
            for instance in data.get("Compute Instances", []):
                writer.writerow({"Compartment": compartment, "Name": instance["name"], "ID": instance["id"]})

    print("Compute instance details saved to 'compute_instances.csv'.")

    # Upload results to Object Storage
    upload_manager = UploadManager(object_storage_client)
    bucket_name = "resource-discovery-results"
    file_path = "oci_resources.json"
    object_name = "oci_resources.json"

    upload_manager.upload_file(
        namespace_name=namespace,
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=file_path
    )
    print(f"Results uploaded to Object Storage bucket '{bucket_name}' as '{object_name}'.")

except oci.exceptions.ServiceError as e:
    print(f"Service Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}")
