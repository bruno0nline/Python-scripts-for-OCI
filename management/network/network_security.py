import oci
import csv

def list_security_lists_and_nsgs():
    config = oci.config.from_file()
    identity_client = oci.identity.IdentityClient(config)
    compartments = identity_client.list_compartments(config["tenancy"], compartment_id_in_subtree=True).data
    network_client = oci.core.VirtualNetworkClient(config)
    
    with open("security_nsg_report.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Compartment", "Type", "Name", "Rule Type", "Protocol", "Source/Destination", "Options", "Remarks"])
        
        for compartment in compartments:
            print(f"Checking compartment: {compartment.name}")
            
            # Fetch Security Lists
            security_lists = network_client.list_security_lists(compartment_id=compartment.id).data
            for sec_list in security_lists:
                for rule in sec_list.ingress_security_rules:
                    remarks = "Open to all (Risky)" if rule.source == "0.0.0.0/0" else "Safe"
                    writer.writerow([compartment.name, "Security List", sec_list.display_name, "Ingress", rule.protocol, rule.source, rule.tcp_options, remarks])
                for rule in sec_list.egress_security_rules:
                    remarks = "Open to all (Risky)" if rule.destination == "0.0.0.0/0" else "Safe"
                    writer.writerow([compartment.name, "Security List", sec_list.display_name, "Egress", rule.protocol, rule.destination, rule.tcp_options, remarks])
            
            # Fetch Network Security Groups (NSGs)
            nsgs = network_client.list_network_security_groups(compartment_id=compartment.id).data
            for nsg in nsgs:
                security_rules = network_client.list_network_security_group_security_rules(network_security_group_id=nsg.id).data
                for rule in security_rules:
                    remarks = "Open to all (Risky)" if rule.source == "0.0.0.0/0" else "Safe"
                    writer.writerow([compartment.name, "NSG", nsg.display_name, rule.direction, rule.protocol, rule.source, "-", remarks])
    
    print("Security and NSG details saved to security_nsg_report.csv")

if __name__ == "__main__":
    list_security_lists_and_nsgs()

