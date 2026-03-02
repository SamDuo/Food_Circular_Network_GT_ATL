// Netlify serverless function: returns ArcGIS API key from environment variable.
// Set ARCGIS_API_KEY in Netlify dashboard → Site settings → Environment variables.

exports.handler = async () => {
  const key = process.env.ARCGIS_API_KEY || "";
  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "no-cache",
    },
    body: JSON.stringify({ arcgisApiKey: key, ARCGIS_API_KEY: key }),
  };
};
