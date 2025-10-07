const width = window.innerWidth;
const height = window.innerHeight;

// Create SVG
const svg = d3.select("body")
  .append("svg")
  .attr("viewBox", [0, 0, width, height]);

// Outer group for zoom
const outerGroup = svg.append("g").attr("id", "zoom-layer");

// Group for each city
const tokyoGroup = outerGroup.append("g").attr("id", "tokyo");   // ← NEW
const parisGroup = outerGroup.append("g").attr("id", "paris");
const nycGroup   = outerGroup.append("g").attr("id", "nyc");

// Tooltip div
const tooltip = d3.select("body").append("div")
  .attr("id", "tooltip")
  .style("position", "absolute")
  .style("display", "none")
  .style("background", "white")
  .style("border", "1px solid gray")
  .style("padding", "4px");

// Projections
// (kept your fixed centers/scales; just added Tokyo and placed it left)
const tokyoProjection = d3.geoMercator()                         // ← NEW
  .center([139.76, 35.68])    // Tokyo center-ish
  .scale(160000)
  .translate([width * 0.15, height / 2]);

const parisProjection = d3.geoMercator()
  .center([2.35, 48.85])      // Paris center
  .scale(130000)
  .translate([width * 0.45, height / 2]);  // nudged to make room

const nycProjection = d3.geoMercator()
  .center([-73.94, 40.72])    // NYC center
  .scale(160000)
  .translate([width * 0.78, height / 2]);

const tokyoPath = d3.geoPath().projection(tokyoProjection);      // ← NEW
const parisPath = d3.geoPath().projection(parisProjection);
const nycPath   = d3.geoPath().projection(nycProjection);

// Shared zoom
svg.call(d3.zoom().on("zoom", ({transform}) => {
  outerGroup.attr("transform", transform);
}));

// Load all three systems
Promise.all([
  // Paris
  d3.json("./data/traces-du-reseau-ferre-idf.geojson"),
  d3.json("./data/emplacement-des-gares-idf-data-generalisee.geojson"),
  // NYC
  d3.json("./data/nyc_subway_routes.geojson"),
  d3.json("./data/nyc_subway_stations.geojson"),
  // Tokyo (NEW)
  d3.json("./filter/data_tokyo/tokyo_subway_routes.geojson"),
  d3.json("./filter/data_tokyo/tokyo_subway_stations.geojson")
]).then(([parisRoutes, parisStations, nycRoutes, nycStations, tokyoRoutes, tokyoStations]) => {

  // --- Tokyo (NEW) ---
  tokyoGroup.selectAll(".tokyo-route")
    .data(tokyoRoutes.features)
    .enter()
    .append("path")
    .attr("class", "tokyo-route")
    .attr("d", tokyoPath)
    .attr("stroke", "#d81b60")   // magenta-ish
    .attr("fill", "none")
    .attr("stroke-width", 1.2)
    .on("mousemove", (event, d) => {
      const p = d.properties || {};
      tooltip.style("display", "block")
        .style("left", event.pageX + 8 + "px")
        .style("top", event.pageY + "px")
        .html(`<strong>${p["name:en"] || p.name || p.ref || ""}</strong>`);
    })
    .on("mouseleave", () => tooltip.style("display", "none"));

  tokyoGroup.selectAll(".tokyo-station")
    .data(tokyoStations.features)
    .enter()
    .append("circle")
    .attr("class", "tokyo-station")
    .attr("r", 2)
    .attr("fill", "#d81b60")
    .attr("cx", d => tokyoProjection(d.geometry.coordinates)[0])
    .attr("cy", d => tokyoProjection(d.geometry.coordinates)[1])
    .on("mousemove", (event, d) => {
      const p = d.properties || {};
      tooltip.style("display", "block")
        .style("left", event.pageX + 8 + "px")
        .style("top", event.pageY + "px")
        .html(`<strong>${p["name:en"] || p.name || ""}</strong>`);
    })
    .on("mouseleave", () => tooltip.style("display", "none"));

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
      const p = d.properties || {};
      tooltip.style("display", "block")
        .style("left", event.pageX + 8 + "px")
        .style("top", event.pageY + "px")
        .html(`<strong>${p.nom_long || p.stop_name || ""}</strong>`);
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
      const p = d.properties || {};
      tooltip.style("display", "block")
        .style("left", event.pageX + 8 + "px")
        .style("top", event.pageY + "px")
        .html(`<strong>${p.stop_name || ""}</strong>`);
    })
    .on("mouseout", () => tooltip.style("display", "none"));
});
