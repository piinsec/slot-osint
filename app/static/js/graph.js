const svg = d3.select("#graph").append("svg")
  .attr("width", "100%").attr("height", "100%")
  .call(d3.zoom().on("zoom", e => g.attr("transform", e.transform)));

const g = svg.append("g");

fetch("/api/graph").then(r => r.json()).then(data => {
  const color = d3.scaleOrdinal()
    .domain(["campaign", "domain", "ip"])
    .range(["#f78166", "#58a6ff", "#3fb950"]);

  const sim = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(60))
    .force("charge", d3.forceManyBody().strength(-120))
    .force("center", d3.forceCenter(window.innerWidth/2, window.innerHeight/2));

  const link = g.selectAll("line").data(data.links).enter().append("line")
    .attr("stroke", "#30363d").attr("stroke-width", 1);

  const node = g.selectAll("circle").data(data.nodes).enter().append("circle")
    .attr("r", d => d.kind === "campaign" ? 8 : d.kind === "domain" ? 5 : 3)
    .attr("fill", d => color(d.kind))
    .call(d3.drag()
      .on("start", (e,d) => { if(!e.active) sim.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; })
      .on("drag",  (e,d) => { d.fx=e.x; d.fy=e.y; })
      .on("end",   (e,d) => { if(!e.active) sim.alphaTarget(0); d.fx=null; d.fy=null; }));

  node.append("title").text(d => `${d.kind}: ${d.label}${d.asn?` (${d.asn})`:''}`);

  const label = g.selectAll("text").data(data.nodes.filter(n => n.kind !== "ip"))
    .enter().append("text").attr("font-size", 10).attr("fill", "#8b949e")
    .text(d => d.label.length > 28 ? d.label.slice(0, 26) + "…" : d.label);

  sim.on("tick", () => {
    link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    node.attr("cx", d => d.x).attr("cy", d => d.y);
    label.attr("x", d => d.x + 6).attr("y", d => d.y + 3);
  });
});