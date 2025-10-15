import fetch from "node-fetch";

export async function handler(event, context) {
  try {
    const data = JSON.parse(event.body || "{}");

    const repoOwner = process.env.REPO_OWNER;
    const repoName = process.env.REPO_NAME;
    const ghToken = process.env.GH_TOKEN;
    const defaultLabel = process.env.DEFAULT_LABEL || "begehung";

    if (!ghToken || !repoOwner || !repoName) {
      throw new Error("GitHub-Konfiguration unvollständig. Bitte Environment-Variablen prüfen.");
    }

    const issueTitle = `${data.title || "Begehung"} – ${data.datum || "Unbekanntes Datum"}`;
    const issueBody = `
    **Ort:** ${data.ort || "-"}
    **Datum:** ${data.datum || "-"}
    **Sifa:** ${data.sifa || "-"}
    **Wetter:** ${data.wetter || "-"}
    **Zusammenfassung:** ${data.summary || "-"}

    ---
    ### Bewertung
    | Kategorie | Status | Bemerkung |
    |------------|--------|------------|
    ${data.categories
      ?.map(
        (c) =>
          `| ${c.label || ""} | ${c.status || ""} | ${c.remark || ""} |`
      )
      .join("\n") || "| - | - | - |"}
    `;

    const ghResponse = await fetch(
      `https://api.github.com/repos/${repoOwner}/${repoName}/issues`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${ghToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: issueTitle,
          body: issueBody,
          labels: [defaultLabel],
        }),
      }
    );

    if (!ghResponse.ok) {
      const errorText = await ghResponse.text();
      throw new Error(`GitHub API Error: ${ghResponse.status} - ${errorText}`);
    }

    const issue = await ghResponse.json();

    return {
      statusCode: 200,
      body: JSON.stringify({
        ok: true,
        issue: issue.html_url,
        number: issue.number,
      }),
    };
  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ ok: false, error: err.message }),
    };
  }
}
