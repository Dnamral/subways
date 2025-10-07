const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("body")
  .append("svg")
  .attr("viewBox", [0, 0, width, height]);

const g = svg.append("g");  // For zooming
const tooltip = d3.select("#tooltip");

// Projection centered on Paris
const projection = d3.geoMercator()
  .center([2.35, 48.85])         // Paris center (approx)
  .scale(100000)                  // Adjust as needed
  .translate([width / 2, height / 2]);

const path = d3.geoPath().projection(projection);

// Zoom/pan behavior
svg.call(d3.zoom().on("zoom", ({transform}) => {
  g.attr("transform", transform);
}));

// Load GeoJSON files
Promise.all([
  d3.json("./data/traces-du-reseau-ferre-idf.geojson"),
  d3.json("./data/emplacement-des-gares-idf-data-generalisee.geojson")
]).then(([routesData, stationsData]) => {

  // Draw routes
  g.selectAll(".route")
    .data(routesData.features)
    .enter()
    .append("path")
    .attr("class", "route")
    .attr("d", path);

  // Draw stations
  g.selectAll(".station")
    .data(stationsData.features)
    .enter()
    .append("circle")
    .attr("class", "station")
    .attr("r", 3)
    .attr("cx", d => projection(d.geometry.coordinates)[0])
    .attr("cy", d => projection(d.geometry.coordinates)[1])
    .on("mouseover", (event, d) => {
      tooltip.style("display", "block")
        .style("left", event.pageX + 8 + "px")
        .style("top", event.pageY + "px")
        .html(`<strong>${d.properties.nom_long || d.properties.nom_zdc || d.properties.nom_zda}</strong>`);
    })
    .on("mouseout", () => {
      tooltip.style("display", "none");
    });
});
