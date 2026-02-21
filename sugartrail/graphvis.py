import networkx as nx
from pathlib import Path
from pyvis.network import Network
from IPython.display import HTML

def visualise_connections(network:list, viz_path):
    """Generates a pyviz force directed graph visualisation from a list of nodes
    showing how they connect. Resulting HTML file saved to viz_path.
    """
    G = nx.DiGraph()
    # Add nodes and edges to the graph
    for item in network:
        node_id = item['id']
        G.add_node(node_id, label=item['title'], type=item['node_type'], depth=item['depth'])
        # Add edges based on link_type and link
        if item['link']:
            G.add_edge(node_id, item['link'], type=item['link_type'])
    # Create a pyvis network using the new graph
    nt = Network(notebook=True, cdn_resources='in_line')
    nt.from_nx(G)
    # Map node_type to corresponding emoji URL
    emoji_urls = {
        "Person": "https://emoji.beeimg.com/👤/240/apple",
        "Company": "https://emoji.beeimg.com/💰/240/apple",
        "Address": "https://emoji.beeimg.com/🏢/240/apple"
    }
    # Update nodes to use the image based on node_type
    for node in nt.nodes:
        node_type = node["type"]  # Get the type from the node
        node["size"] = 30
        if node_type in emoji_urls:
            node["image"] = emoji_urls[node_type]
            # check if node is origin node:
            if node["depth"] == 0:
                node["image"] = "https://emoji.beeimg.com/🌐/240/apple"
                node["color"] = "white"
                node["shape"] = "circularImage"
            else:
                node["shape"] = "image"
    for edge in nt.edges:
        edge["color"] = "black"
    # Enable physics
    nt.toggle_physics(True)
    physics_options = """
    {
        "physics": {
            "solver": "barnesHut",
            "barnesHut": {
                "gravitationalConstant": -10000,
                "centralGravity": 0.3,
                "springLength": 100,
                "springConstant": 0.05,
                "damping": 0.09,
                "avoidOverlap": 0.5
            },
            "minVelocity": 0.75,
            "maxVelocity": 5
        }
    }
    """
    nt.set_options(physics_options)
    # Save to file and display inline (avoids IFrame browser URL issues)
    html_path = Path(viz_path) / 'graph.html'
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_content = nt.generate_html()
    html_path.write_text(html_content)
    return HTML(html_content)
