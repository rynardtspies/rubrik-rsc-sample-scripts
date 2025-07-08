
Write-Output "Retrieving SLA details from Rubrik..."

# Import the Rubrik PowerShell module
Import-Module RubrikSecurityCloud
# Connect to the Rubrik cluster
Connect-Rsc

$query = @"
    query GetSlaDomains(`$after`: String) {
        slaDomains (after: `$after) {
            pageInfo {
                startCursor
                endCursor
                hasPreviousPage
                hasNextPage
            }
            count
            edges {
                node {
                    ... on GlobalSlaReply {
                        name 
                        id
                        snapshotSchedule {
                            hourly {
                                basicSchedule {
                                    frequency
                                    retention
                                    retentionUnit
                                }
                            }
                            daily {
                                basicSchedule {
                                    frequency
                                    retention
                                    retentionUnit
                                }
                            }
                            weekly {
                                basicSchedule {
                                    frequency
                                    retention
                                    retentionUnit
                                }
                            }
                            monthly {
                                basicSchedule {
                                    frequency
                                    retention
                                    retentionUnit
                                }
                            }
                            yearly {
                                basicSchedule {
                                    frequency
                                    retention
                                    retentionUnit
                                }
                            }
                        }
                    }
                }
            }
        }
    }
"@

# Get the SLA Domain details
$slaDomains = Invoke-Rsc -GqlQuery $query

Write-Output($slaDomains.count.edges)
# Display the SLA Domain details
$slaDomains.edges | ForEach-Object {
    Write-Output "SLA Domain Name: $($_.node.name)"
    Write-Output "SLA Domain ID: $($_.node.id)"
    Write-Output "----------------------------------------"
}
# Disconnect from the Rubrik cluster
Disconnect-Rsc