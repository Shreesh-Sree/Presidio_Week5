"""AlgoQX Studio -- Agent Builder Frontend Page."""

from __future__ import annotations

import json
import streamlit as st
import httpx

from frontend.components.ui import page_header, glass_card, metric_card, status_badge

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the Agent Builder canvas and topological routing controls."""
    page_header(
        title="Agent Builder",
        subtitle="Design complex multi-agent execution graphs using LangGraph with human-in-the-loop steps.",
    )

    # State variables for canvas nodes
    if "agent_nodes" not in st.session_state:
        st.session_state.agent_nodes = [
            {"id": "node_1", "type": "planner", "label": "Planner Node", "x": 100, "y": 150},
            {"id": "node_2", "type": "researcher", "label": "Web Researcher", "x": 300, "y": 150},
        ]
    if "agent_edges" not in st.session_state:
        st.session_state.agent_edges = [
            {"source": "node_1", "target": "node_2", "label": "plan"}
        ]

    # HTML Drag and drop Canvas Component
    nodes_json = json.dumps(st.session_state.agent_nodes)
    edges_json = json.dumps(st.session_state.agent_edges)

    canvas_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                background-color: #0a0a0f;
                color: #e2e8f0;
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 10px;
                overflow: hidden;
            }}
            #canvas {{
                width: 100%;
                height: 480px;
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                background-color: #0e0e15;
                position: relative;
                overflow: hidden;
                box-shadow: inset 0 0 20px rgba(0,0,0,0.6);
            }}
            .node {{
                position: absolute;
                width: 140px;
                padding: 10px;
                background-color: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 8px;
                cursor: move;
                text-align: center;
                user-select: none;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                transition: border-color 0.15s, box-shadow 0.15s;
            }}
            .node:hover {{
                border-color: #6366f1;
                box-shadow: 0 0 12px rgba(99,102,241,0.25);
            }}
            .node-planner {{ border-left: 4px solid #6366f1; }}
            .node-researcher {{ border-left: 4px solid #06b6d4; }}
            .node-retriever {{ border-left: 4px solid #10b981; }}
            .node-reasoner {{ border-left: 4px solid #f59e0b; }}
            .node-writer {{ border-left: 4px solid #a855f7; }}
            .node-reviewer {{ border-left: 4px solid #ef4444; }}
            .node-title {{
                font-size: 0.8rem;
                font-weight: 600;
                margin-bottom: 4px;
            }}
            .node-type {{
                font-size: 0.65rem;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            svg {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 0;
            }}
            #palette {{
                display: flex;
                gap: 10px;
                margin-bottom: 12px;
            }}
            .palette-btn {{
                background-color: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
                color: #e2e8f0;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.75rem;
                font-weight: 500;
                transition: background-color 0.15s;
            }}
            .palette-btn:hover {{
                background-color: rgba(99,102,241,0.15);
                border-color: #6366f1;
            }}
        </style>
    </head>
    <body>
        <div id="palette">
            <button class="palette-btn" onclick="addNode('planner')">+ Planner</button>
            <button class="palette-btn" onclick="addNode('researcher')">+ Researcher</button>
            <button class="palette-btn" onclick="addNode('retriever')">+ Retriever</button>
            <button class="palette-btn" onclick="addNode('reasoner')">+ Reasoner</button>
            <button class="palette-btn" onclick="addNode('writer')">+ Writer</button>
            <button class="palette-btn" onclick="addNode('reviewer')">+ Reviewer</button>
            <button class="palette-btn" onclick="clearCanvas()" style="border-color:#ef4444; color:#ef4444;">Clear</button>
        </div>

        <div id="canvas" ondragover="allowDrop(event)">
            <svg id="svg-connections">
                <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1" />
                    </marker>
                </defs>
            </svg>
        </div>

        <script>
            let nodes = {nodes_json};
            let edges = {edges_json};
            let draggedNode = null;
            let activeNodeId = null;

            function init() {{
                renderNodes();
                renderConnections();
            }}

            function renderNodes() {{
                const canvas = document.getElementById('canvas');
                // Clear existing nodes
                document.querySelectorAll('.node').forEach(n => n.remove());

                nodes.forEach(n => {{
                    const el = document.createElement('div');
                    el.id = n.id;
                    el.className = `node node-${{n.type}}`;
                    el.style.left = n.x + 'px';
                    el.style.top = n.y + 'px';
                    el.innerHTML = `
                        <div class="node-title">${{n.label}}</div>
                        <div class="node-type">${{n.type}}</div>
                    `;
                    el.addEventListener('mousedown', (e) => startDrag(e, n));
                    canvas.appendChild(el);
                }});
            }}

            function renderConnections() {{
                const svg = document.getElementById('svg-connections');
                // Keep only defs
                const defs = svg.querySelector('defs');
                svg.innerHTML = '';
                svg.appendChild(defs);

                edges.forEach(edge => {{
                    const sourceNode = document.getElementById(edge.source);
                    const targetNode = document.getElementById(edge.target);

                    if (sourceNode && targetNode) {{
                        const sourceRect = sourceNode.getBoundingClientRect();
                        const targetRect = targetNode.getBoundingClientRect();
                        const canvasRect = document.getElementById('canvas').getBoundingClientRect();

                        const x1 = sourceNode.offsetLeft + 140;
                        const y1 = sourceNode.offsetTop + 20;
                        const x2 = targetNode.offsetLeft;
                        const y2 = targetNode.offsetTop + 20;

                        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                        // Curve path
                        const dx = Math.abs(x2 - x1) * 0.5;
                        const d = `M ${{x1}} ${{y1}} C ${{x1 + dx}} ${{y1}}, ${{x2 - dx}} ${{y2}}, ${{x2}} ${{y2}}`;
                        
                        path.setAttribute('d', d);
                        path.setAttribute('stroke', '#6366f1');
                        path.setAttribute('stroke-width', '2');
                        path.setAttribute('fill', 'none');
                        path.setAttribute('marker-end', 'url(#arrow)');

                        svg.appendChild(path);
                    }}
                }});
            }}

            function startDrag(e, node) {{
                draggedNode = node;
                activeNodeId = node.id;
                const shiftX = e.clientX - e.target.closest('.node').getBoundingClientRect().left + document.getElementById('canvas').getBoundingClientRect().left;
                const shiftY = e.clientY - e.target.closest('.node').getBoundingClientRect().top + document.getElementById('canvas').getBoundingClientRect().top;

                function moveAt(clientX, clientY) {{
                    const canvasRect = document.getElementById('canvas').getBoundingClientRect();
                    let newX = clientX - canvasRect.left - (e.clientX - e.target.closest('.node').getBoundingClientRect().left);
                    let newY = clientY - canvasRect.top - (e.clientY - e.target.closest('.node').getBoundingClientRect().top);

                    // Bound to canvas
                    newX = Math.max(10, Math.min(newX, canvasRect.width - 150));
                    newY = Math.max(10, Math.min(newY, canvasRect.height - 60));

                    node.x = newX;
                    node.y = newY;

                    const el = document.getElementById(node.id);
                    if (el) {{
                        el.style.left = newX + 'px';
                        el.style.top = newY + 'px';
                    }}
                    renderConnections();
                }}

                function onMouseMove(e) {{
                    moveAt(e.clientX, e.clientY);
                }}

                document.addEventListener('mousemove', onMouseMove);

                document.addEventListener('mouseup', function onMouseUp() {{
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                    draggedNode = null;
                    sendDataToStreamlit();
                }});
            }}

            function addNode(type) {{
                const id = 'node_' + (nodes.length + 1) + '_' + Math.floor(Math.random() * 100);
                const label = type.charAt(0).toUpperCase() + type.slice(1) + ' Node';
                const canvasRect = document.getElementById('canvas').getBoundingClientRect();
                const x = 50 + (nodes.length * 40) % (canvasRect.width - 200);
                const y = 100 + (nodes.length * 20) % (canvasRect.height - 150);

                const newNode = {{ id, type, label, x, y }};
                nodes.push(newNode);

                // Add connection to previous node automatically
                if (nodes.length > 1) {{
                    edges.push({{
                        source: nodes[nodes.length - 2].id,
                        target: id,
                        label: 'flow'
                    }});
                }}

                renderNodes();
                renderConnections();
                sendDataToStreamlit();
            }}

            function clearCanvas() {{
                nodes = [];
                edges = [];
                renderNodes();
                renderConnections();
                sendDataToStreamlit();
            }}

            function allowDrop(e) {{
                e.preventDefault();
            }}

            function sendDataToStreamlit() {{
                const data = {{ nodes, edges }};
                // Post message to Streamlit container
                window.parent.postMessage({{
                    type: 'streamlit:message',
                    data: data
                }}, '*');
            }}

            window.onload = init;
        </script>
    </body>
    </html>
    """

    col_canvas, col_config = st.columns([3, 1])

    with col_canvas:
        st.components.v1.html(canvas_html, height=540, scrolling=False)

    with col_config:
        st.markdown("### Agent Config")

        # Global Config Controls
        # Fetch available models from backend
        agent_model_options = []
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{API_BASE}/api/llm/models")
                if res.status_code == 200:
                    agent_model_options = [m["id"] for m in res.json().get("models", [])]
        except Exception:
            pass
        
        if not agent_model_options:
            st.error("⚠️ Unable to fetch models from backend. Please ensure the backend server is running.")
            st.stop()
        
        model = st.selectbox(
            "Target Model",
            options=agent_model_options,
        )

        selected_tools = st.multiselect(
            "Equip Tools",
            options=["web_search", "calculator", "code_executor", "wikipedia", "file_reader"],
            default=["web_search", "calculator"],
        )

        memory_enabled = st.checkbox("Persistent Memory", value=True)
        human_approval = st.checkbox("Human Approval (HITL)", value=False)

    st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)

    # Input execution triggers
    agent_input = st.text_area(
        "Enter query statement for the Agent Network",
            placeholder="Enter your task description...",
        height=80,
    )

    if st.button("Run Multi-Agent Graph"):
        if not agent_input.strip():
            st.warning("Please enter a query statement.")
        else:
            with st.spinner("Executing multi-agent flow..."):
                try:
                    payload = {
                        "config": {
                            "nodes": st.session_state.agent_nodes,
                            "edges": st.session_state.agent_edges,
                            "tools": selected_tools,
                            "memory_enabled": memory_enabled,
                            "human_approval": human_approval,
                        },
                        "input_text": agent_input,
                        "model": model,
                    }

                    with httpx.Client(timeout=60.0) as client:
                        res = client.post(
                            f"{API_BASE}/api/agent/execute",
                            json=payload,
                        )

                    if res.status_code == 200:
                        data = res.json()

                        # Summary Output
                        st.markdown("#### Final Agent Response")
                        st.markdown(glass_card(data["output"]), unsafe_allow_html=True)

                        # Execution Timeline Steps
                        st.markdown("<br>#### Execution Steps Timeline", unsafe_allow_html=True)
                        for idx, step in enumerate(data["steps"]):
                            step_num = idx + 1
                            badge_style = "info"
                            if step["node_type"] == "planner":
                                badge_style = "success"
                            elif step["node_type"] == "reviewer":
                                badge_style = "error"

                            status_badge_html = status_badge(step["node_type"].upper(), badge_style)
                            time_cost_html = f"Latency: {step['latency_ms']:.1f}ms"

                            st.markdown(
                                f"""
                                <div class='glass-card' style='margin-bottom:12px;'>
                                    <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                                        <span>Step {step_num}: {status_badge_html} <b>{step['node_id']}</b></span>
                                        <span style='font-size:0.75rem; color:var(--text-muted);'>{time_cost_html}</span>
                                    </div>
                                    <div style='font-size:0.875rem;'>{step['output_text']}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            # If tools were executed
                            if step["tool_calls"]:
                                for tc in step["tool_calls"]:
                                    st.markdown(
                                        f"&nbsp;&nbsp;&nbsp;&nbsp;🔧 **Tool Executed**: `{tc['tool']}` (Status: {tc['status']})"
                                    )

                except Exception as e:
                    st.error(f"Failed to execute multi-agent graph: {e}")
