import oci
import openpyxl
from openpyxl.styles import Font

def collect_unused_resources():
    config = oci.config.from_file()
    identity_client = oci.identity.IdentityClient(config)
    blockstorage_client = oci.core.BlockstorageClient(config)
    compute_client = oci.core.ComputeClient(config)
    network_client = oci.core.VirtualNetworkClient(config)
    object_storage_client = oci.object_storage.ObjectStorageClient(config)
    file_storage_client = oci.file_storage.FileStorageClient(config)
    compute_management_client = oci.core.ComputeManagementClient(config)
    load_balancer_client = oci.load_balancer.LoadBalancerClient(config)
    
    tenancy_id = config["tenancy"]
    print("Fetching compartments...")
    compartments = identity_client.list_compartments(
        tenancy_id, compartment_id_in_subtree=True
    ).data
    
    availability_domains = identity_client.list_availability_domains(tenancy_id).data
    
    # Create an Excel workbook
    workbook = openpyxl.Workbook()
    
    # Define sheet names
    sheets = {
        "Unattached Volumes": ["Compartment", "Volume Name", "Volume OCID", "Size (GB)", "State", "Created Time", "Last Backup Time", "Remarks"],
        "Orphaned Instances": ["Compartment", "Instance Name", "Instance OCID", "State", "Shape", "Created Time", "Remarks"],
        "Unused Storage": ["Compartment", "Bucket Name / File System", "Type", "Size (GB)", "State", "Created Time", "Remarks"],
        "Unattached VNICs": ["Compartment", "VNIC Name", "VNIC OCID", "State", "Created Time", "Remarks"],
        "Orphaned Load Balancers": ["Compartment", "Load Balancer Name", "Load Balancer OCID", "State", "Created Time", "Remarks"],
        "Unused Public IPs": ["Compartment", "Public IP", "Assigned To", "State", "Created Time", "Remarks"],
        "Inactive DRGs & VPNs": ["Compartment", "Resource Name", "Type", "State", "Created Time", "Remarks"]
    }

    sheet_objects = {}
    for sheet_name, headers in sheets.items():
        sheet = workbook.create_sheet(title=sheet_name)
        sheet.append(headers)
        # Apply bold font to headers
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        sheet_objects[sheet_name] = sheet
    
    # Remove default sheet
    workbook.remove(workbook["Sheet"])

    for compartment in compartments:
        print(f"Checking compartment: {compartment.name}")
        
        # Unattached Volumes
        volumes = blockstorage_client.list_volumes(compartment_id=compartment.id).data
        for volume in volumes:
            if volume.lifecycle_state != "AVAILABLE":
                continue
            sheet_objects["Unattached Volumes"].append([
                compartment.name, volume.display_name, volume.id,
                volume.size_in_gbs, volume.lifecycle_state,
                volume.time_created.strftime('%Y-%m-%d %H:%M:%S'), "N/A", "Unattached"
            ])
        
        # Orphaned Compute Instances
        instances = compute_client.list_instances(compartment_id=compartment.id).data
        for instance in instances:
            if instance.lifecycle_state in ["TERMINATED", "STOPPED"]:
                sheet_objects["Orphaned Instances"].append([
                    compartment.name, instance.display_name, instance.id,
                    instance.lifecycle_state, instance.shape,
                    instance.time_created.strftime('%Y-%m-%d %H:%M:%S'), "Orphaned"
                ])

        # Unused Object Storage Buckets & File Storage
        namespace = object_storage_client.get_namespace().data
        buckets = object_storage_client.list_buckets(namespace, compartment_id=compartment.id).data
        for bucket in buckets:
            bucket_details = object_storage_client.get_bucket(namespace, bucket.name).data
            bucket_size = bucket_details.approximate_size if bucket_details.approximate_size is not None else 0
            remarks = "Unused" if bucket_details.approximate_count == 0 else "Active"
            sheet_objects["Unused Storage"].append([
                compartment.name, bucket.name, "Object Storage", 
                bucket_size / (1024 * 1024 * 1024), "Available",
                bucket.time_created.strftime('%Y-%m-%d %H:%M:%S'), remarks
            ])
        
        for ad in availability_domains:
            file_systems = file_storage_client.list_file_systems(compartment_id=compartment.id, availability_domain=ad.name).data
            for fs in file_systems:
                remarks = "Unused" if fs.lifecycle_state == "AVAILABLE" else "In Use"
                sheet_objects["Unused Storage"].append([
                    compartment.name, fs.display_name, "File Storage", "N/A", 
                    fs.lifecycle_state, fs.time_created.strftime('%Y-%m-%d %H:%M:%S'), remarks
                ])
        
        # Unattached VNICs
        vnic_attachments = compute_client.list_vnic_attachments(compartment_id=compartment.id).data
        for vnic in vnic_attachments:
            if vnic.lifecycle_state != "ATTACHED":
                sheet_objects["Unattached VNICs"].append([
                    compartment.name, vnic.display_name, vnic.id,
                    vnic.lifecycle_state, vnic.time_created.strftime('%Y-%m-%d %H:%M:%S'), "Unattached"
                ])
        
        # Orphaned Load Balancers
        load_balancers = load_balancer_client.list_load_balancers(compartment_id=compartment.id).data
        for lb in load_balancers:
            if lb.lifecycle_state in ["TERMINATED", "FAILED"]:
                sheet_objects["Orphaned Load Balancers"].append([
                    compartment.name, lb.display_name, lb.id,
                    lb.lifecycle_state, lb.time_created.strftime('%Y-%m-%d %H:%M:%S'), "Orphaned"
                ])
        
        # Unused Public IPs
        public_ips = network_client.list_public_ips(scope="REGION", compartment_id=compartment.id).data
        for ip in public_ips:
            assigned_to = ip.assigned_entity_id if ip.assigned_entity_id else "Unassigned"
            sheet_objects["Unused Public IPs"].append([
                compartment.name, ip.ip_address, assigned_to,
                ip.lifecycle_state, ip.time_created.strftime('%Y-%m-%d %H:%M:%S'), "Unused"
            ])
        
        # Inactive DRGs & VPNs
        drgs = network_client.list_drgs(compartment_id=compartment.id).data
        for drg in drgs:
            if drg.lifecycle_state != "AVAILABLE":
                sheet_objects["Inactive DRGs & VPNs"].append([
                    compartment.name, drg.display_name, "DRG", drg.lifecycle_state,
                    drg.time_created.strftime('%Y-%m-%d %H:%M:%S'), "Inactive"
                ])

    # Save the Excel file
    workbook.save("unused_resources_report.xlsx")
    print("Unused resources report saved to unused_resources_report.xlsx")

if __name__ == "__main__":
    collect_unused_resources()
