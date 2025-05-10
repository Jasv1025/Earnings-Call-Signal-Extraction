export default async function handler(req, res) {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      transcript: "any",
      provider: "ollama", // or "openai"
    }),
  });

  const data = await response.json();
  res.status(200).json(data);
}