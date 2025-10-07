const width = window.innerWidth;
const height = window.innerHeight;

// Create SVG
const svg = d3.select("body")
  .append("svg")
  .attr("viewBox", [0, 0, width, height]);

// Outer group for zoom
const outerGroup = svg.append("g").attr("id", "zoom-layer");

// Group for each city
const parisGroup = outerGroup.append("g").attr("id", "paris");
const nycGroup = outerGroup.append("g").attr("id", "nyc");

// Tooltip div
const tooltip = d3.select("body").append("div")
  .attr("id", "tooltip")
  .style("position", "absolute")
  .style("display", "none")
  .style("background", "white")
  .style("border", "1px solid gray")
  .style("padding", "4px");

// Projections
const parisProjection = d3.geoMercator()
  .center([2.35, 48.85])              // Paris center
  .scale(130000)                      // You may adjust for readability
  .translate([width * 0.3, height / 2]);

const nycProjection = d3.geoMercator()
  .center([-73.94, 40.72])            // NYC center
  .scale(160000)
  .translate([width * 0.7, height / 2]);

const parisPath = d3.geoPath().projection(parisProjection);
const nycPath = d3.geoPath().projection(nycProjection);

// Shared zoom
svg.call(d3.zoom().on("zoom", ({transform}) => {
  outerGroup.attr("transform", transform);
}));

// Load both systems
Promise.all([
  d3.json("./data/traces-du-reseau-ferre-idf.geojson"),
  d3.json("./data/emplacement-des-gares-idf-data-generalisee.geojson"),
  d3.json("./data/nyc_subway_routes.geojson"),
  d3.json("./data/nyc_subway_stations.geojson")
]).then(([parisRoutes, parisStations, nycRoutes, nycStations]) => {

  // --- Paris ---
  parisGroup.selectAll(".paris-route")
    .data(parisRoutes.features)
    .enter()
    .append("path")
    .attr("class", "paris-route")
    .attr("d", parisPath)
    .attr("stroke", "purple")
    .attr("fill", "none")
    .attr("stroke-width", 1.2);

  parisGroup.selectAll(".paris-station")
    .data(parisStations.features)
    .enter()
    .append("circle")
    .attr("class", "paris-station")
    .attr("r", 2)
    .attr("fill", "purple")
    .attr("cx", d => parisProjection(d.geometry.coordinates)[0])
    .attr("cy", d => parisProjection(d.geometry.coordinates)[1])
    .on("mouseover", (event, d) => {
      tooltip.style("display", "block")
        .style("left", event.pageX + 8 + "px")
        .style("top", event.pageY + "px")
        .html(`<strong>${d.properties.nom_long || d.properties.stop_name}</strong>`);
    })
    .on("mouseout", () => tooltip.style("display", "none"));

  // --- NYC ---
  nycGroup.selectAll(".nyc-route")
    .data(nycRoutes.features)
    .enter()
    .append("path")
    .attr("class", "nyc-route")
    .attr("d", nycPath)
    .attr("stroke", "black")
    .attr("fill", "none")
    .attr("stroke-width", 1.2);

  nycGroup.selectAll(".nyc-station")
    .data(nycStations.features)
    .enter()
    .append("circle")
    .attr("class", "nyc-station")
    .attr("r", 2)
    .attr("fill", "black")
    .attr("cx", d => nycProjection(d.geometry.coordinates)[0])
    .attr("cy", d => nycProjection(d.geometry.coordinates)[1])
    .on("mouseover", (event, d) => {
      tooltip.style("display", "block")
        .style("left", event.pageX + 8 + "px")
        .style("top", event.pageY + "px")
        .html(`<strong>${d.properties.stop_name}</strong>`);
    })
    .on("mouseout", () => tooltip.style("display", "none"));
});
