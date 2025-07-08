import requests, os, csv, argparse, json
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

# A class to define the GraphQL queries
class Queries():
    @staticmethod
    def get_sla_domains(after_cursor: str = None):
        """Get SLA domains with pagination support."""
        query = """
            query GetSlaDomains($after: String) {
                slaDomains (after: $after) {
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
        """

        variables = None
        if after_cursor is not None:
            variables = {
                "after" : after_cursor
            }

        return dict (
            query=query,
            variables=variables
        )
    

# A class to connect and send requests to the Rubrik API (RSC)
class RubrikClient:
    def __init__(self, client_id=None, client_secret=None, env_name=None):
        self.base_url = f"https://{env_name}.my.rubrik.com"
        self.token = None
        self.client_id = client_id if client_id else os.getenv('RUBRIK_CLIENT_ID')
        self.client_secret = client_secret if client_secret else os.getenv('RUBRIK_CLIENT_SECRET')
        self.headers = {'Content-Type': 'application/json'}
        self._authenticate()


    def _authenticate(self):
        """Authenticate with the Rubrik API using client credentials."""
        url = f"{self.base_url}/api/client_token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            self.token = response.json().get('access_token')

            self.headers['Authorization'] = f"Bearer {self.token}"
            print("Connected to RSC...")
        else:
            raise Exception(f"Authentication failed: {response.text}")

    
    def _delete_session(self):
        """Delete the current session."""
        if self.token:
            url = f"{self.base_url}/api/session"
            response = requests.delete(url, headers=self.headers)
            if response.status_code in [200, 204]:
                print("Session deleted successfully.")
                self.token = None
                print(f"Disconnected from RSC.")
            else:
                raise Exception(f"Failed to delete session: {response.text}")
        else:
            print("No active session to delete.")


    def _send_graphql_call(self, payload):
        """Send a GraphQL cal to the Rubrik API and return the JSON response."""
        url = f"{self.base_url}/api/graphql"
        payload = payload
        response = requests.post(url, json=payload, headers=self.headers)
        if response.ok:
            return response.json()
        else:
            raise Exception(f"GraphQL query failed: {response.text}")


    def _get_sla_domains(self):
        """Retrieve all SLA domains with pagination support."""
        after_cursor = None
        hasnextpage = True
        sladomains = []

        while hasnextpage:
            slaDomains_payload = Queries.get_sla_domains(after_cursor=after_cursor)
            response = self._send_graphql_call(payload=slaDomains_payload)
            sladomains_page = response.get("data", {}).get("slaDomains", {})
            sladomains.extend(sladomains_page.get("edges", []))
            pageInfo = sladomains_page.get("pageInfo", {})
            hasnextpage = pageInfo.get("hasNextPage", False)
            after_cursor = pageInfo.get("endCursor", None)
            print(f"\tSLA domains retrieved so far: {len(sladomains)}. end_cursor: {after_cursor}")
        return sladomains
    
    

# MAIN SCRIPT
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rubrik CDM nodes..")
    parser.add_argument("--client_id", help="Client ID for Rubrik API authentication. Defaults to RUBRIK_CLIENT_ID environment variable if not provided.", default=None)
    parser.add_argument("--client_secret", help="Client Secret for Rubrik API authentication. Defaults to RUBRIK_CLIENT_SECRET environment variable if not provided.", default=None)
    parser.add_argument("--env_name", help="Environment name for the Rubrik Security Cloud instance. Example: 'rscetf' for 'rscetf.my.rubrik.com'. Do not include the domain names.", default=None)

    args = parser.parse_args()

    client = RubrikClient(client_id=args.client_id, client_secret=args.client_secret, env_name=args.env_name)

    print("Retrieving SLA domains...")
    sladomains = client._get_sla_domains()
    print(f"Total SLA domains retrieved: {len(sladomains)}")
    for sladomain in sladomains:
        print(f"SLA Domain Name: {sladomain['node']['name']}, ID: {sladomain['node']['id']}")
        #print(f"Snapshot Schedule: {sladomain['node']['snapshotSchedule']}")
        snapshot_schedule = sladomains[0]['node']['snapshotSchedule']
        for schedule_type, schedule in snapshot_schedule.items():
            if schedule and 'basicSchedule' in schedule:
                basic_schedule = schedule['basicSchedule']
                print(f"{schedule_type.capitalize()} Schedule: Frequency: {basic_schedule['frequency']}, Retention: {basic_schedule['retention']} {basic_schedule['retentionUnit']}")
            else:
                print(f"{schedule_type.capitalize()} Schedule: Not configured")
        print("\n")

    if not sladomains:
        print("No SLA domains found.")
        client._delete_session()
        exit(0)
    
    # Clean up the session
    client._delete_session()


    print("Cleaning up...")