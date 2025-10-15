export async function handler(event, context) {
  return {
    statusCode: 200,
    body: JSON.stringify({
      ok: true,
      message: "Function läuft!",
      test: true
    }),
  };
}
