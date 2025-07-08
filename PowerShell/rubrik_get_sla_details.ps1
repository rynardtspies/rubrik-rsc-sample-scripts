
Write-Output "Retrieving SLA details from Rubrik..."

# Import the Rubrik PowerShell module
Import-Module RubrikSecurityCloud
# Connect to the Rubrik cluster
Connect-Rsc
# Get the SLA Domain details
$slaDomains = Get-RscSla
# Display the SLA Domain details
$slaDomains | ForEach-Object {
    Write-Output "SLA Domain Name: $($_.name)"
    Write-Output "SLA Domain ID: $($_.id)"
    Write-Output "----------------------------------------"
}
# Disconnect from the Rubrik cluster
Disconnect-Rsc