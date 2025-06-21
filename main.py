
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uuid
import asyncio
from typing import List
from fastapi.responses import HTMLResponse
import json
import os

from wiki_crawler import crawl_chain
app = FastAPI()


# todo - settings module
SESSIONS_FILE = "sessions.json"

# load from file - if not create
if os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, "r") as f:
        sessions = json.load(f)
else:
    sessions = {}

def save_sessions():
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)

class ChainRequest(BaseModel):
    title: str

# endpoints 
@app.post("/start_chain/{start_title}")
async def start_chain(start_title: str):
    # avoid uuid - its so messy - sorry copilot
    title = start_title.strip().replace(" ", "_")
    chain_id = title.lower()
    if title.lower() in (s["title"].lower() for s in sessions.values()):
        for k, v in sessions.items():
            if v["title"].lower() == title.lower():
                return {"chain_id": k, "status": "duplicate"}

    sessions[chain_id] = {"title": title, "status": "running", "result": []}
    save_sessions()
    asyncio.create_task(run_chain(title, chain_id))
    return {"chain_id": chain_id, "status": "started"}

# need working - leaderboard 
@app.get("/leaderboard")
async def get_leaderboard():
    leaderboard = sorted(
        [(k, v["title"], v["status"]) for k, v in sessions.items() if v["status"] == "finished"],
        key=lambda x: x[1].lower()
    )
    #return leaderboard
    # return sessions
    return sorted(sessions.items(), key=lambda x: x[1]["title"].lower()) # ?????

@app.get("/status/")
async def get_status():
    return [{"chain_id": chain_id, "status": sessions[chain_id]["status"], "steps": len(sessions[chain_id]["result"])} for chain_id in sessions]

@app.get("/chain/{chain_id}")
async def get_chain(chain_id: str):
    if chain_id not in sessions:
        raise HTTPException(status_code=404, detail="Chain not found")
    return sessions[chain_id]

@app.get("/visualize/{chain_id}")
async def visualize_chain(chain_id: str):
    if chain_id not in sessions:
        raise HTTPException(status_code=404, detail="Chain not found")
    result = sessions[chain_id]["result"]
    nodes = list({url: {"id": url} for url in result}.values())
    links = [
        {"source": result[i], "target": result[i+1]}
        for i in range(len(result) - 1)
    ]
    return {"nodes": nodes, "links": links}

@app.get("/visualize_multi")
async def visualize_multi(chain_ids: List[str] = Query(...)):
    all_results = {}
    for cid in chain_ids:
        if cid not in sessions:
            raise HTTPException(status_code=404, detail=f"Chain {cid} not found")
        all_results[cid] = sessions[cid]["result"]

    # Merge nodes and links
    node_counts = {}
    link_set = set()
    nodes = []
    links = []

    for cid, result in all_results.items():
        for url in result:
            node_counts[url] = node_counts.get(url, 0) + 1
        for i in range(len(result) - 1):
            link = (result[i], result[i+1], cid)
            if link not in link_set:
                link_set.add(link)
                links.append({"source": link[0], "target": link[1], "chain": cid})

    for url, count in node_counts.items():
        title = url.split("/wiki/")[-1].replace("_", " ")
        nodes.append({"id": url, "label": title, "shared": count > 1})

    return {"nodes": nodes, "links": links}



async def run_chain(title, chain_id):
    result = await crawl_chain(title, 1000)
    sessions[chain_id]["result"] = result
    sessions[chain_id]["status"] = "finished"


    save_sessions()



# v1 stat pae
@app.get("/status_page", response_class=HTMLResponse)
async def status_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wikipedia Chain Statsus</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Wikipedia Chain Status</h1>
        <div>
        <input type="text" id="start_chain" placeholder="Paste Wiki Link..." style="width:80%; align: left; height: 30px;">
        <button id="start_button" style=" width:18%; align: right; height: 30px; ">Start Chain</button>
        </div>
        <table id="status-table">
            <thead>
                <tr>
                <th>Selection</th>
                <th>Chain ID</th>
                <th>Link</th>
                <th>Status</th></tr>
            </thead>
            <tbody></tbody>
        </table>
        
        <text id="status_message" style="margin-top: 10px;"></text>
        <br>
        <button id="graph" style="padding: 10px; margin-top: 10px;">View Multi Graphs</button>
        <script>
            async function fetchStatus() {
                const response = await fetch('/status/');
                const data = await response.json();
                const tbody = document.querySelector('#status-table tbody');

                tbody.innerHTML = '';
                data.forEach(chain => {
                    const row = document.createElement('tr');
                    selection = `<input type="checkbox" class="chain-select" value="${chain.chain_id}">`;
                    link = `/graph-echarts?chain_ids=${chain.chain_id}`;
                    hyperlink = `<a href="${link}" target="_blank">${chain.chain_id}</a>`;
                    row.innerHTML = `<td>${selection}</td><td>${chain.chain_id}</td><td>${hyperlink}</td><td>${chain.status}</td>`;
                    tbody.appendChild(row);

                });
            }
            setInterval(fetchStatus, 5000);
            fetchStatus();
            document.getElementById("graph").addEventListener("click", () => {
                const selectedChains = Array.from(document.querySelectorAll('.chain-select:checked'))
                    .map(checkbox => checkbox.value);
                if (selectedChains.length === 0) {
                    alert("Please select at least one chain to visualize.");
                    return;
                }
                const url = `/graph-echarts?chain_ids=${selectedChains.join('&chain_ids=')}`;
                window.open(url, '_blank');
            });




            document.getElementById("start_chain").addEventListener("keypress", (event) => {
                if (event.key === "Enter") {
                    document.getElementById("start_button").click();
                }
            });
            document.getElementById("start_button").addEventListener("click", async () => {
                const title = document.getElementById("start_chain").value.trim().replace("https://en.wikipedia.org/wiki/", "").replace(" ", "_");
                if (!title) {
                    alert("Please enter a valid Wikipedia title.");
                    document.getElementById("status_message").innerText = "Please enter a valid Wikipedia title.";
                    return;
                }
                const response = await fetch(`/start_chain/${encodeURIComponent(title)}`, { method: 'POST' });
                if (response.ok) {
                    const data = await response.json();
                    alert(`Chain started with ID: ${data.chain_id}`);
                    document.getElementById("status_message").innerText = `Chain started with ID: ${data.chain_id}`;
                    document.getElementById("start_chain").value = '';
                } else {
                    const errorData = await response.json();
                    alert(`Error: ${errorData.detail}`);
                    document.getElementById("status_message").innerText = `Error: ${errorData.detail}`;
                }
            });

        </script>
    </body>
    </html>
    """

# new stat page - echart - iframe 
@app.get("/status-page-v2", response_class=HTMLResponse)
async def status_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wikipedia Chain Status & Graph</title>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                padding: 20px;
                margin: 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: #fff;
            }
            th, td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
            #chart {
                width: 100%;
                height: 500px;
                margin-top: 30px;
                background: white;
                border: 1px solid #ccc;
            }
        </style>
    </head>
    <body>
        <h1>Wikipedia Chain Tracker</h1>

        <div>
            <input type="text" id="start_chain" placeholder="Paste Wiki Link or Title..." style="width:80%; height: 30px;">
            <button id="start_button" style="width:18%; height: 30px;">Start Chain</button>
        
            <button id="leaderboard" style="padding: 10px; margin-top: 10px;">View Leaderboard</button>
            <button id="random" style="padding: 10px; margin-top: 10px;">Start Random Chain</button>
        </div>

        <table id="status-table">
            <thead>
                <tr><th>Select</th>
                <th>Chain ID</th>
                <th>Link</th>
                <th>Status</th>
                <th>Steps</th>
                
                </tr>
            </thead>
            <tbody></tbody>
        </table>

        <p id="status_message" style="color: green;"></p>
        <button id="graph" style="padding: 10px; margin-top: 10px;">Render Selected Graphs</button>

        <div id="chart"></div>

        <script>
            async function fetchStatus() {
                const response = await fetch('/status/');
                const data = await response.json();
                const tbody = document.querySelector('#status-table tbody');
                tbody.innerHTML = '';
                data.forEach(chain => {
                    const row = document.createElement('tr');
                    const link = `/graph-echarts?chain_ids=${chain.chain_id}`;
                    row.innerHTML = `
                        <td><input type="checkbox" class="chain-select" value="${chain.chain_id}"></td>
                        <td>${chain.chain_id}</td>
                        <td><a href="${link}" target="_blank">${chain.chain_id}</a></td>
                        <td>${chain.status}</td>
                        <td>${chain.steps || 0}</td>`;
                    tbody.appendChild(row);
                });
            }

            async function renderGraph(chainIds) {
                const chart = echarts.init(document.getElementById('chart'));
                const url = `/visualize_multi?${chainIds.map(id => `chain_ids=${id}`).join('&')}`;
                const response = await fetch(url);
                const data = await response.json();

                const nodeMap = {};
                const nodes = data.nodes.map(n => {
                    const label = n.label || n.id.split('/wiki/').pop().replace(/_/g, ' ');
                    nodeMap[n.id] = label;
                    return {
                        id: n.id,
                        name: label,
                        value: 5,
                        symbolSize: n.shared ? 20 : 12,
                        tooltip: {
                            formatter: `<b>${label}</b><br><a href='${n.id}' target='_blank'>Open Wikipedia</a>`
                        },
                        itemStyle: {
                            color: n.shared ? 'gold' : '#69b3a2',
                            borderColor: n.shared ? 'crimson' : '#333',
                            borderWidth: n.shared ? 2 : 1
                        }
                    };
                });

                const links = data.links.map(l => ({
                    source: l.source,
                    target: l.target,
                    lineStyle: {
                        color: '#aaa',
                        opacity: 0.6
                    }
                }));

                const option = {
                    tooltip: {
                        trigger: 'item',
                        formatter: function (params) {
                            return params.data.tooltip?.formatter || params.name;
                        }
                    },
                    series: [{
                        type: 'graph',
                        layout: 'force',
                        roam: false,
                        draggable: true,
                        zoom: 1.2,
                        label: {
                            show: true,
                            position: 'right',
                            formatter: '{b}'
                        },
                        emphasis: {
                            focus: 'adjacency',
                            label: { show: true }
                        },
                        force: {
                            repulsion: 100,
                            edgeLength: [30, 70]
                        },
                        data: nodes,
                        links: links,
                        lineStyle: {
                            width: 1,
                            curveness: 0.3
                        }
                    }]
                };

                chart.setOption(option);

                chart.on('click', params => {
                    if (params.dataType === 'node' && params.data.id) {
                        window.open(params.data.id, '_blank');
                    }
                });
            }

            document.getElementById("graph").addEventListener("click", () => {
                const selected = Array.from(document.querySelectorAll('.chain-select:checked')).map(cb => cb.value);
                if (selected.length === 0) {
                    alert("Select at least one chain to visualize.");
                    return;
                }
                renderGraph(selected);
            });

            document.getElementById("start_button").addEventListener("click", async () => {
                const title = document.getElementById("start_chain").value.trim().replace("https://en.wikipedia.org/wiki/", "").replace(/ /g, "_");
                if (!title) {
                    alert("Please enter a Wikipedia page title.");
                    return;
                }
                const res = await fetch(`/start_chain/${encodeURIComponent(title)}`, { method: 'POST' });
                const result = await res.json();
                document.getElementById("status_message").innerText = `Chain started: ${result.chain_id}`;
                document.getElementById("start_chain").value = '';
                fetchStatus();
            });

            document.getElementById("leaderboard").addEventListener("click", async () => {
                const response = await fetch('/leaderboard');
                const leaderboard = await response.json();
                
                for (const [chain_id, session] of Object.entries(leaderboard)) {
                    message += `Chain ID: ${chain_id}, Title: ${session.title}, Status: ${session.status}\n`;  

                }
                alert(message);
                document.getElementById("status_message").innerText = message;
            });
            document.getElementById("random").addEventListener("click", async () => {
    // Step 1: Get a random title from Wikipedia API
    const apiUrl = "https://en.wikipedia.org/w/api.php?action=query&list=random&rnnamespace=0&rnlimit=1&format=json&origin=*";

    const wikiResponse = await fetch(apiUrl);
    const wikiData = await wikiResponse.json();
    const title = wikiData.query.random[0].title.replace(/ /g, "_");

    // Step 2: Call your backend with the title
    const response = await fetch(`/start_chain/${encodeURIComponent(title)}`, {
        method: 'POST'
    });

    const result = await response.json();
    document.getElementById("status_message").innerText = `Random chain started: ${result.chain_id}`;
    document.getElementById("start_chain").value = '';
    fetchStatus();
});

            // Allow pressing Enter to start chain  

            document.getElementById("start_chain").addEventListener("keypress", e => {
                if (e.key === "Enter") document.getElementById("start_button").click();
            });

            setInterval(fetchStatus, 5000);
            fetchStatus();
        </script>
    </body>
    </html>
    """



# single graph echarts 
@app.get("/graph-echarts", response_class=HTMLResponse)
async def graph_page_echarts():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Wikipedia Chain Graph — ECharts</title>
      <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
      <style>
        html, body, #chart { width: 100%; height: 100%; margin: 0; padding: 0; }
      </style>
    </head>
    <body>
      <div id="chart"></div>
      <script>
        const params = new URLSearchParams(window.location.search);
        const ids = params.getAll('chain_ids');
        fetch(`/visualize_multi?${ids.map(id=>`chain_ids=${id}`).join('&')}`)
          .then(res => res.json())
          .then(data => {
            const nodeMap = {};
            data.nodes.forEach(n => {
              nodeMap[n.id] = { name: n.label, value: 5, itemStyle: {
                color: n.shared ? 'gold' : '#69b3a2',
                borderColor: n.shared ? 'crimson' : '#333',
                borderWidth: n.shared ? 2 : 1
              }};
            });

            const series = {
              type: 'graph',
              layout: 'force',
              roam: false,
              draggable: true,
              zoom: 1.2,
              force: { repulsion: 100, edgeLength: [20, 50] },
              label: { show: true, formatter: '{b}', position: 'right' },
              emphasis: { focus: 'adjacency', label: { show: true } },
              data: data.nodes.map(n => ({
                id: n.id, name: n.label,
                symbolSize: n.shared ? 20 : 12,
                ...nodeMap[n.id]
              })),
              edges: data.links.map(l => ({
                source: l.source, target: l.target,
                lineStyle: { color: '#999', width: 1 }
              }))
            };

            const chart = echarts.init(document.getElementById('chart'));
            chart.setOption({ series: [series] });

            chart.on('click', params => {
              if (params.dataType === 'node' && params.data.id) {
                window.open(params.data.id, '_blank');
              }
            });
          });
      </script>
    </body>
    </html>
    """






