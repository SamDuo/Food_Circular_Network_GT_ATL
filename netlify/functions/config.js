// Netlify serverless function: returns ArcGIS API key from environment variable.
// Set ARCGIS_API_KEY in Netlify dashboard → Site settings → Environment variables.

exports.handler = async () => {
  const arcgis = process.env.ARCGIS_API_KEY || "";
  const mapbox = process.env.MAPBOX_PUBLIC_KEY || "";
  const tomtom = process.env.TOMTOM_API_KEY || "";
  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "no-cache",
    },
    body: JSON.stringify({
      arcgisApiKey: arcgis,
      ARCGIS_API_KEY: arcgis,
      mapboxPublicKey: mapbox,
      tomtomApiKey: tomtom,
    }),
  };
};
