import requests

def graphql_call(endpoint, query, variables={}):
    r = requests.post(endpoint, json={"query": query, "variables": variables})
    if r.status_code == 200:
        # print(json.dumps(r.json(), indent=2))
        return r.json()["data"]
    else:
        raise Exception(f"Query failed to run with a {r.status_code}.")

def get_subgraph_details(subgraph_deployment_ids, network = 'mainnet'):
    if not isinstance(subgraph_deployment_ids, list):
        subgraph_deployment_ids = [subgraph_deployment_ids]
    endpoint = (
       "https://api.thegraph.com/subgraphs/name/"
       "graphprotocol/graph-network-" + network
    )

    query = """query subgraphDetails($ipfsHash: [String!]!){
        subgraphDeployments(where:{
           ipfsHash_in: $ipfsHash
        })
        {
            ipfsHash
            originalName
            versions(orderBy:entityVersion, orderDirection:desc,first:1){
                subgraph{
                    currentVersionRelationEntity{
                        subgraph{
                        displayName
                        }
                        deployment{
                        ipfsHash
                        }
                    }
                }
            }
        }
    }
    """
    variables = {'ipfsHash': subgraph_deployment_ids}
    response = graphql_call(endpoint, query, variables)
    return response["subgraphDeployments"]