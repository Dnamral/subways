const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("body")
  .append("svg")
  .attr("viewBox", [0, 0, width, height]);

const g = svg.append("g");  // For zooming
const tooltip = d3.select("#tooltip");

// Originally scaled at 80000 : perfect for protein comparison
// 40000 : More a thumbnail
const projection = d3.geoMercator()
  .center([-73.94, 40.72]) // NYC-ish center
  .scale(160000)
  .translate([width / 2, height / 2]);

const path = d3.geoPath().projection(projection);

// Zoom/pan behavior
svg.call(d3.zoom().on("zoom", ({transform}) => {
  g.attr("transform", transform);
}));

// Load GeoJSON files
Promise.all([
  d3.json("./data/nyc_subway_routes.geojson"),
  d3.json("./data/nyc_subway_stations.geojson")
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
        .html(`<strong>${d.properties.stop_name}</strong>`);
    })
    .on("mouseout", () => {
      tooltip.style("display", "none");
    });
});
